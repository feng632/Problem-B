import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common

import numpy as np
import joblib as jb
from scipy.optimize import minimize as lbfgsb

from pymoo.core.problem import Problem
from pymoo.core.variable import Real, Integer, Choice
from pymoo.core.mixed import (
    MixedVariableSampling,
    MixedVariableMating,
    MixedVariableDuplicateElimination,
)
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.optimize import minimize as pymoo_minimize

res = jb.load(common.DATA_DIR / "gpr.pkl")
scaler = res["_scaler"]
outputs = [k for k in res.keys() if not k.startswith("_")]  # ["Rth", "dP", "dT"], 顺序与 W 对应
gprs = {col: res[col]["gpr"] for col in outputs}

BETA_LEVELS = [3.0, 3.5, 4.0, 4.5]  # 附件2里beta实际只有这4档离散取值

# 可行域(04-models.tex 5.3.1,eq:q3-constraints,main分支更新版):
# x1 in {0} U [0.10, 0.30], x3 in {0} U {2,...,10}, 耦合: alpha=0 <=> n=0
X1_FINNED_BOUNDS = (0.10, 0.30)
X3_FINNED_RANGE = range(2, 11)
W = np.array([1 / 3, 1 / 3, 1 / 3])  # 权重,对应 (Rth, dP, dT)

# 全体合法离散(x2,x3)组合:无针肋模式(x3=0,搭配x1=0) + 有针肋模式(x3=2..10,x1连续可调)
ALL_COMBOS = (
    [(x2, 0) for x2 in BETA_LEVELS]
    + [(x2, x3) for x2 in BETA_LEVELS for x3 in X3_FINNED_RANGE]
)


def predict(X: np.ndarray) -> np.ndarray:
    """X: (n, 3) 原始尺度 [alpha, beta, n] -> F: (n, 3) [Rth, dP, dT]"""
    X_std = scaler.transform(X)
    return np.column_stack([gprs[col].predict(X_std) for col in outputs])


# ---------- 第一步:全局多目标搜索(混合变量 NSGA-II,mode 变量处理耦合约束) ----------

def to_physical(x):
    """x: pymoo mixed-variable dict {mode, x1, x2, x3} -> [alpha, beta, n] 物理坐标"""
    if x["mode"] == 0:
        return [0.0, x["x2"], 0]
    return [x["x1"], x["x2"], x["x3"]]


class SinkOptProblem(Problem):
    def __init__(self):
        super().__init__(
            vars={
                "mode": Choice(options=[0, 1]),  # 0=无针肋, 1=有针肋
                "x1": Real(bounds=X1_FINNED_BOUNDS),
                "x2": Choice(options=BETA_LEVELS),
                "x3": Integer(bounds=(X3_FINNED_RANGE.start, X3_FINNED_RANGE.stop - 1)),
            },
            n_obj=3,
        )

    def _evaluate(self, X, out, *args, **kwargs):
        arr = np.array([to_physical(x) for x in X])
        out["F"] = predict(arr)


def run_nsga2(pop_size=100, n_gen=200, seed=676767):
    problem = SinkOptProblem()
    algorithm = NSGA2(
        pop_size=pop_size,
        sampling=MixedVariableSampling(),
        mating=MixedVariableMating(eliminate_duplicates=MixedVariableDuplicateElimination()),
        eliminate_duplicates=MixedVariableDuplicateElimination(),
    )
    result = pymoo_minimize(
        problem, algorithm,
        termination=("n_gen", n_gen),
        seed=seed,
        verbose=False,
    )
    X_front = np.array([to_physical(x) for x in result.X])
    F_front = result.F
    return X_front, F_front


def run_nsga2_multiseed(pop_size=200, n_gen=300, seeds=range(10)):
    """单次 NSGA-II 前沿不稳定(存在多个局部盆地),多种子跑完拼接前沿。"""
    X_all, F_all = [], []
    for seed in seeds:
        X_front, F_front = run_nsga2(pop_size=pop_size, n_gen=n_gen, seed=seed)
        X_all.append(X_front)
        F_all.append(F_front)
    return np.vstack(X_all), np.vstack(F_all)


# ---------- 第二步:归一化基准(GPR 在合法可行域内的预测值域) ----------

def gpr_value_range(n1=25):
    """在合法可行域(无针肋点集 + 有针肋规则网格)上取 GPR 预测值的 min/max"""
    x2_arr = np.array(BETA_LEVELS)
    X_finless = np.column_stack([np.zeros_like(x2_arr), x2_arr, np.zeros_like(x2_arr)])

    x1 = np.linspace(*X1_FINNED_BOUNDS, n1)
    x3 = np.arange(X3_FINNED_RANGE.start, X3_FINNED_RANGE.stop)
    g1, g2, g3 = np.meshgrid(x1, x2_arr, x3, indexing="ij")
    X_finned = np.column_stack([g1.ravel(), g2.ravel(), g3.ravel()])

    F = predict(np.vstack([X_finless, X_finned]))
    return F.min(axis=0), F.max(axis=0)


def normalize(F, f_min, f_max):
    return (F - f_min) / (f_max - f_min)


# ---------- 第三步:理想点法/加权综合最优 —— 穷举全部合法(x2,x3)组合 + L-BFGS-B精修x1 ----------

def ideal_point_distance(F_norm, w=W):
    return np.sqrt(np.sum(w * F_norm ** 2, axis=1))


def refine_at_fixed_x2x3(x2, x3, x1_init, f_min, f_max, w=W):
    """固定 (x2, x3): x3=0 时 x1 必须=0(无针肋,直接求值);否则对 x1 在 [0.10,0.30] 做 L-BFGS-B 精修"""
    def D_of(x1_val):
        F = predict(np.array([[x1_val, x2, x3]]))[0]
        F_norm = (F - f_min) / (f_max - f_min)
        return np.sqrt(np.sum(w * F_norm ** 2))

    if x3 == 0:
        return 0.0, D_of(0.0)

    def obj(x1):
        return D_of(x1[0])

    x0 = min(max(x1_init, X1_FINNED_BOUNDS[0]), X1_FINNED_BOUNDS[1])
    result = lbfgsb(obj, x0=[x0], bounds=[X1_FINNED_BOUNDS], method="L-BFGS-B")
    return result.x[0], result.fun


def global_best(w, f_min, f_max, x1_inits=(0.10, 0.15, 0.20, 0.25, 0.30)):
    """穷举全部40种合法(x2,x3)组合,每种对x1多起点精修,取全局D最小 -> (x1*,x2*,x3*,D*)"""
    best = None
    for x2, x3 in ALL_COMBOS:
        inits = (0.0,) if x3 == 0 else x1_inits
        for x1_init in inits:
            x1_r, D_r = refine_at_fixed_x2x3(x2, x3, x1_init, f_min, f_max, w=w)
            if best is None or D_r < best[3]:
                best = (x1_r, x2, x3, D_r)
    return best


def solve(pop_size=200, n_gen=300, seeds=range(10)):
    X_front, F_front = run_nsga2_multiseed(pop_size=pop_size, n_gen=n_gen, seeds=seeds)
    f_min, f_max = gpr_value_range()

    # NSGA-II前沿上按理想点距离选出的"预精修"最优,仅用于回代验证对照
    F_norm = normalize(F_front, f_min, f_max)
    D_front = ideal_point_distance(F_norm)
    pre_idx = np.argmin(D_front)
    x_pre = X_front[pre_idx]
    D_pre = D_front[pre_idx]
    F_pre = F_front[pre_idx]

    # 穷举全部合法离散组合 + L-BFGS-B精修,得到最终综合最优方案
    x1_star, x2_star, x3_star, D_star = global_best(W, f_min, f_max)
    F_star = predict(np.array([[x1_star, x2_star, x3_star]]))[0]

    # 回代验证偏差: GA前沿上的预精修解 vs 精修后的最终解,相对偏差(%)
    rel_dev = np.abs(F_star - F_pre) / np.abs(F_pre) * 100

    print(f"Pareto front size: {len(X_front)}")
    print(f"pre-refine best on front: x1={x_pre[0]:.4f} x2={x_pre[1]:.2f} x3={int(x_pre[2])} D={D_pre:.6f}")
    print(f"refined optimum X*: x1={x1_star:.4f} x2={x2_star:.2f} x3={x3_star} D={D_star:.6f}")
    print(f"predicted Rth={F_star[0]:.4f} dP={F_star[1]:.4f} dT={F_star[2]:.4f}")
    print(f"回代验证相对偏差(%): Rth={rel_dev[0]:.4f} dP={rel_dev[1]:.4f} dT={rel_dev[2]:.4f}")

    out = {
        "X_front": X_front, "F_front": F_front,
        "f_min": f_min, "f_max": f_max,
        "x_star": (x1_star, x2_star, x3_star),
        "F_star": F_star,
        "D_star": D_star,
        "rel_dev_pct": rel_dev,
    }
    jb.dump(out, common.DATA_DIR / "q3_result.pkl")
    return out


if __name__ == "__main__":
    solve()

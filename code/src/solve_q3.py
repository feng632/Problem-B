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

BOUNDS = {
    "x1": (0.00, 0.30),   # alpha 针肋宽度比(连续)
    "x2": BETA_LEVELS,    # beta  歧管深高比(离散,4档)
    "x3": (0, 10),        # n     针肋排数(整数)
}
W = np.array([1 / 3, 1 / 3, 1 / 3])  # 权重,对应 (Rth, dP, dT)


def predict(X: np.ndarray) -> np.ndarray:
    """X: (n, 3) 原始尺度 [alpha, beta, n] -> F: (n, 3) [Rth, dP, dT]"""
    X_std = scaler.transform(X)
    return np.column_stack([gprs[col].predict(X_std) for col in outputs])


# ---------- 第一步:全局多目标搜索(混合变量 NSGA-II) ----------

class SinkOptProblem(Problem):
    def __init__(self):
        super().__init__(
            vars={
                "x1": Real(bounds=BOUNDS["x1"]),
                "x2": Choice(options=BETA_LEVELS),
                "x3": Integer(bounds=BOUNDS["x3"]),
            },
            n_obj=3,
        )

    def _evaluate(self, X, out, *args, **kwargs):
        # X 是长度 n_pop 的 dict 数组(mixed variable),转成 (n, 3) 矩阵
        arr = np.array([[x["x1"], x["x2"], x["x3"]] for x in X])
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
    # result.X: 长度 n_front 的 dict 数组; result.F: (n_front, 3)
    X_front = np.array([[x["x1"], x["x2"], x["x3"]] for x in result.X])
    F_front = result.F
    return X_front, F_front


# ---------- 第二步:归一化基准(直接用 GPR 在决策空间的预测值域) ----------

def gpr_value_range(n1=25):
    """在决策空间内取规则网格(x2 取全部4档, x3 取全部整数排),用 GPR 预测值的 min/max 作为 f_j,min / f_j,max"""
    x1 = np.linspace(*BOUNDS["x1"], n1)
    x2 = np.array(BETA_LEVELS)
    x3 = np.arange(BOUNDS["x3"][0], BOUNDS["x3"][1] + 1)
    g1, g2, g3 = np.meshgrid(x1, x2, x3, indexing="ij")
    X = np.column_stack([g1.ravel(), g2.ravel(), g3.ravel()])
    F = predict(X)
    return F.min(axis=0), F.max(axis=0)


def normalize(F, f_min, f_max):
    return (F - f_min) / (f_max - f_min)


# ---------- 第三步:理想点法选综合最优 + 整数邻域 L-BFGS-B 精修 ----------

def ideal_point_distance(F_norm, w=W):
    return np.sqrt(np.sum(w * F_norm ** 2, axis=1))


def refine_at_fixed_x2x3(x2, x3, x1_init, f_min, f_max, w=W):
    """固定 (x2, x3)(离散),只对 x1 做 L-BFGS-B 精修,最小化 D(X)"""
    def obj(x1):
        X = np.array([[x1[0], x2, x3]])
        F = predict(X)[0]
        F_norm = (F - f_min) / (f_max - f_min)
        return np.sqrt(np.sum(w * F_norm ** 2))

    result = lbfgsb(
        obj, x0=[x1_init],
        bounds=[BOUNDS["x1"]],
        method="L-BFGS-B",
    )
    return result.x[0], result.fun


def run_nsga2_multiseed(pop_size=200, n_gen=300, seeds=range(10)):
    """单次 NSGA-II 在这个问题上前沿不稳定(存在多个局部盆地),
    多种子跑完把前沿拼在一起,让理想点选择建立在更完整的前沿上。"""
    X_all, F_all = [], []
    for seed in seeds:
        X_front, F_front = run_nsga2(pop_size=pop_size, n_gen=n_gen, seed=seed)
        X_all.append(X_front)
        F_all.append(F_front)
    return np.vstack(X_all), np.vstack(F_all)


def solve(pop_size=200, n_gen=300, seeds=range(10)):
    X_front, F_front = run_nsga2_multiseed(pop_size=pop_size, n_gen=n_gen, seeds=seeds)
    f_min, f_max = gpr_value_range()

    F_norm = normalize(F_front, f_min, f_max)
    D = ideal_point_distance(F_norm)
    best_idx = np.argmin(D)
    x1_0, x2_0, x3_0 = X_front[best_idx]
    x3_0 = int(round(x3_0))

    # 离散邻域网格搜索:x2 取全部4档、x3 在最优解附近 +-1 排内逐个精修 x1,比较 D
    candidates = []
    for x2_cand in BETA_LEVELS:
        for x3_cand in range(max(BOUNDS["x3"][0], x3_0 - 1), min(BOUNDS["x3"][1], x3_0 + 1) + 1):
            x1_r, D_r = refine_at_fixed_x2x3(x2_cand, x3_cand, x1_0, f_min, f_max)
            candidates.append((x1_r, x2_cand, x3_cand, D_r))

    x1_star, x2_star, x3_star, D_star = min(candidates, key=lambda c: c[3])

    print(f"Pareto front size: {len(X_front)}")
    print(f"best on front (pre-refine): x1={x1_0:.4f} x2={x2_0:.4f} x3={x3_0} D={D[best_idx]:.6f}")
    print(f"refined optimum: x1={x1_star:.4f} x2={x2_star:.4f} x3={x3_star} D={D_star:.6f}")

    F_star = predict(np.array([[x1_star, x2_star, x3_star]]))[0]
    print(f"predicted Rth={F_star[0]:.6f} dP={F_star[1]:.6f} dT={F_star[2]:.6f}")

    out = {
        "X_front": X_front, "F_front": F_front,
        "f_min": f_min, "f_max": f_max,
        "x_star": (x1_star, x2_star, x3_star),
        "F_star": F_star,
        "D_star": D_star,
    }
    jb.dump(out, common.DATA_DIR / "q3_result.pkl")
    return out


if __name__ == "__main__":
    solve()

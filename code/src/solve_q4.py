import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common

import numpy as np
import joblib as jb

import solve_q3 as q3

# ---------- 权重场景 ----------

SCENARIOS = {
    "高性能计算": np.array([0.6, 0.2, 0.2]),
    "便携/低功耗设备": np.array([0.2, 0.6, 0.2]),
    "高可靠工业器件": np.array([0.2, 0.2, 0.6]),
}


def simplex_grid(n=6):
    """重心坐标网格: w = (i/n, j/n, (n-i-j)/n), i+j<=n, 天然满足 sum(w)=1"""
    pts = []
    for i in range(n + 1):
        for j in range(n + 1 - i):
            k = n - i - j
            pts.append([i / n, j / n, k / n])
    return np.array(pts)


# 给定权重求最优解:直接复用 solve_q3.global_best(合法(x2,x3)组合穷举 + 一维L-BFGS-B精修x1)
solve_weighted = q3.global_best


# ---------- 第一部分(1)(2): 权重扫描 ----------

def weight_sweep(weights, f_min, f_max):
    """对一批权重逐个求最优解,返回 X*(W), D*(W)"""
    X_star = np.zeros((len(weights), 3))
    D_star = np.zeros(len(weights))
    for i, w in enumerate(weights):
        x1, x2, x3, D = solve_weighted(w, f_min, f_max)
        X_star[i] = [x1, x2, x3]
        D_star[i] = D
    return X_star, D_star


# ---------- 第一部分(3): 敏感性矩阵(单纯形内保约束的中心差分) ----------

def perturb_weight(w0, j, h):
    """沿第j个权重方向扰动 h,同时从另外两个权重里等量扣除,保持 sum(w)=1"""
    dw = -h / 2 * np.ones(3)
    dw[j] = h
    w = w0 + dw
    return w


def sensitivity_matrix(w0, f_min, f_max, h=0.05):
    """S[i,j] = d x_i / d w_j,中心差分,i in {x1,x2,x3}, j in {w1,w2,w3}"""
    S = np.zeros((3, 3))
    for j in range(3):
        w_plus = perturb_weight(w0, j, h)
        w_minus = perturb_weight(w0, j, -h)
        if (w_plus < 0).any() or (w_minus < 0).any():
            # 靠近单纯形边界时缩小步长,避免扰动出界
            h_local = min(w0[j], (1 - w0[j]) / 2, h) * 0.5
            w_plus = perturb_weight(w0, j, h_local)
            w_minus = perturb_weight(w0, j, -h_local)
            h_use = h_local
        else:
            h_use = h
        x_plus = np.array(solve_weighted(w_plus, f_min, f_max)[:3])
        x_minus = np.array(solve_weighted(w_minus, f_min, f_max)[:3])
        S[:, j] = (x_plus - x_minus) / (2 * h_use)
    return S


# ---------- 第二部分: minimax regret 鲁棒设计 ----------

def minimax_regret(candidates, weight_grid, f_min, f_max, D_star_grid):
    """candidates: (n,3) 候选X池; weight_grid/D_star_grid: 权重采样点及其D*(W)
    返回每个候选的最大后悔值,及取最大后悔值最小的鲁棒解"""
    F_cand = q3.predict(candidates)
    F_norm_cand = q3.normalize(F_cand, f_min, f_max)  # (n_cand, 3)

    max_regret = np.full(len(candidates), -np.inf)
    for w, D_opt in zip(weight_grid, D_star_grid):
        D_w = np.sqrt(np.sum(w * F_norm_cand ** 2, axis=1))  # (n_cand,)
        regret = D_w - D_opt
        max_regret = np.maximum(max_regret, regret)

    robust_idx = np.argmin(max_regret)
    return robust_idx, max_regret


def cv_of_candidate(X, weight_grid, f_min, f_max):
    """CV(X) = std(D_W(X))/mean(D_W(X)),在权重网格上评估单个候选X的稳健性(离散系数)"""
    F = q3.predict(np.array([X]))[0]
    F_norm = (F - f_min) / (f_max - f_min)
    D_w = np.sqrt(np.sum(weight_grid * F_norm ** 2, axis=1))
    return D_w.std() / D_w.mean()


def solve():
    f_min, f_max = q3.gpr_value_range()

    # ---- (1)(2) 权重扫描: 3个典型场景 + 单纯形网格 ----
    scenario_names = list(SCENARIOS.keys())
    scenario_w = np.array(list(SCENARIOS.values()))
    grid_w = simplex_grid(n=6)
    all_w = np.vstack([scenario_w, grid_w])

    X_star, D_star = weight_sweep(all_w, f_min, f_max)

    print("== 权重扫描: 3个典型场景 ==")
    for name, w, x, d in zip(scenario_names, all_w[:3], X_star[:3], D_star[:3]):
        print(f"{name} w={w}: x1={x[0]:.4f} x2={x[1]:.2f} x3={int(x[2])} D={d:.6f}")
    print(f"单纯形网格采样点数: {len(grid_w)}")

    # ---- (3) 敏感性矩阵: 在3个典型场景处各算一个 ----
    print("\n== 敏感性矩阵 S[i,j]=dx_i/dw_j (在3个典型场景处) ==")
    sens_matrices = {}
    for name, w in zip(scenario_names, scenario_w):
        S = sensitivity_matrix(w, f_min, f_max)
        sens_matrices[name] = S
        print(f"-- {name} --")
        print(S)

    # ---- 第二部分: minimax regret 鲁棒方案 ----
    q3_res = jb.load(common.DATA_DIR / "q3_result.pkl")
    candidates = q3_res["X_front"]  # 复用Q3的Pareto前沿当候选池
    D_star_equal = q3_res["D_star"]  # Q3等权重(1/3,1/3,1/3)下的D*,作为epsilon基准

    robust_idx, max_regret = minimax_regret(candidates, all_w, f_min, f_max, D_star)
    x_robust = candidates[robust_idx]
    R_max = max_regret[robust_idx]
    epsilon = 0.05 * D_star_equal  # eq:minimax: epsilon = 5% * D*(等权重Q3最优值)

    cv_robust = cv_of_candidate(x_robust, all_w, f_min, f_max)
    cv_equal = cv_of_candidate(np.array(q3_res["x_star"]), all_w, f_min, f_max)

    print(f"\n== 鲁棒方案 (minimax regret) ==")
    print(f"X_robust: x1={x_robust[0]:.4f} x2={x_robust[1]:.2f} x3={int(round(x_robust[2]))}")
    print(f"R_max = {R_max:.6f}   epsilon(5%*D*_Q3) = {epsilon:.6f}   R_max<=epsilon: {R_max <= epsilon}")
    print(f"CV(X_robust) = {cv_robust:.6f}   CV(X*_Q3等权重解) = {cv_equal:.6f}")

    out = {
        "f_min": f_min, "f_max": f_max,
        "scenario_names": scenario_names, "scenario_w": scenario_w,
        "all_w": all_w, "X_star": X_star, "D_star": D_star,
        "sens_matrices": sens_matrices,
        "candidates": candidates, "max_regret": max_regret,
        "x_robust": x_robust, "robust_idx": robust_idx,
        "R_max": R_max, "epsilon": epsilon,
        "cv_robust": cv_robust, "cv_equal": cv_equal,
    }
    jb.dump(out, common.DATA_DIR / "q4_result.pkl")
    return out


if __name__ == "__main__":
    solve()

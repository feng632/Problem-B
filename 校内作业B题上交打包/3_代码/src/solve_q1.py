import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common

import numpy as np
import pandas as pd
import joblib as jb
from scipy.optimize import curve_fit
from sklearn.metrics import r2_score, mean_absolute_percentage_error

file = common.DATA_DIR / "data.xlsx"
data = pd.read_excel(file, header=1).rename(columns={
    "样本编号": "index",
    "针肋宽度比": "alpha",
    "歧管深高比": "beta",
    "单个歧管单元内沿流向的针肋排数": "n",
    "无量纲热阻": "Rth",
    "无量纲压降": "dP",
    "无量纲温度非均匀性": "dT",
})

# ---------- 1.1 半经验关联式标定 ----------
# dP* = C * beta^a * (1-alpha)^b * n^c : 幂律,取对数后线性最小二乘。
# n=0(无针肋)的4个样本不满足幂律结构(没有"逐排叠加"的物理机制),排除在此拟合外。
FINNED = data[data["n"] > 0].copy()


def fit_dp_corr(df):
    y = np.log(df["dP"].to_numpy())
    X = np.column_stack([
        np.ones(len(df)),
        np.log(df["beta"].to_numpy()),
        np.log(1 - df["alpha"].to_numpy()),
        np.log(df["n"].to_numpy()),
    ])
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    lnC, a, b, c = coef
    C = np.exp(lnC)
    dp_pred = C * df["beta"] ** a * (1 - df["alpha"]) ** b * df["n"] ** c
    r2 = r2_score(df["dP"], dp_pred)
    mape = mean_absolute_percentage_error(df["dP"], dp_pred)
    return {"C": C, "a": a, "b": b, "c": c, "r2": r2, "mape": mape, "pred": dp_pred}


def rth_model(X, R0, c1, c2, c3, c4, alpha_star):
    alpha, beta, n = X
    # 基础式(eq:rth-corr)只有R0/c1/c2/c3四项时R2=0.61(<0.9),FILL_CHECKLIST建议
    # 加alpha*n交互项(排数对热阻的边际影响随宽度比变化)——加了之后R2升到0.75,
    # 仍不到0.9但明显改善,MAPE本来就很低(<1%,Rth数值范围本身很窄0.72~0.77,
    # R2对窄量程数据天然不友好);已按建议加了交互项,R2仍偏低的情况在notes.md
    # 里记录,留给建模手判断是否需要进一步改结构。
    return R0 + c1 * (alpha - alpha_star) ** 2 + c2 * beta + c3 * n + c4 * alpha * n


def fit_rth_corr(df):
    X = (df["alpha"].to_numpy(), df["beta"].to_numpy(), df["n"].to_numpy())
    y = df["Rth"].to_numpy()
    p0 = [0.75, 0.1, 0.0, 0.0, 0.0, 0.2]  # alpha*初值取拐点附近0.2(论文预期)
    popt, _ = curve_fit(rth_model, X, y, p0=p0, maxfev=20000)
    R0, c1, c2, c3, c4, alpha_star = popt
    rth_pred = rth_model(X, *popt)
    r2 = r2_score(y, rth_pred)
    mape = mean_absolute_percentage_error(y, rth_pred)
    return {"R0": R0, "c1": c1, "c2": c2, "c3": c3, "c4": c4, "alpha_star": alpha_star,
            "r2": r2, "mape": mape, "pred": rth_pred}


# ---------- 1.2 影响幅度定量表(用GPR代理模型做控制变量分析,数据网格不满不能直接分组平均) ----------

res = jb.load(common.DATA_DIR / "gpr.pkl")
scaler = res["_scaler"]
gpr_outputs = [k for k in res.keys() if not k.startswith("_")]
gprs = {col: res[col]["gpr"] for col in gpr_outputs}


def avg_relative_change(alpha1, alpha2, beta_grid, n_grid, out_col):
    """固定(beta,n)遍历网格,统计 out_col 从 alpha1 到 alpha2 的平均相对变化(%)"""
    changes = []
    for beta in beta_grid:
        for n in n_grid:
            X = np.array([[alpha1, beta, n], [alpha2, beta, n]])
            X_std = scaler.transform(X)
            y = gprs[out_col].predict(X_std)
            changes.append((y[1] - y[0]) / y[0] * 100)
    return np.mean(changes)


def influence_table():
    BETA_G = [3.0, 3.5, 4.0, 4.5]
    N_G = [2, 4, 6, 8, 10]
    ALPHA_G = [0.10, 0.15, 0.20, 0.30]

    rows = {}
    # alpha 影响: Rth先降后升, dP总体增大
    rows["alpha_010_020_Rth"] = avg_relative_change(0.10, 0.20, BETA_G, N_G, "Rth")
    rows["alpha_020_030_Rth"] = avg_relative_change(0.20, 0.30, BETA_G, N_G, "Rth")
    rows["alpha_010_030_dP"] = avg_relative_change(0.10, 0.30, BETA_G, N_G, "dP")
    # beta 影响: dP、dT总体减小
    rows["beta_300_450_dP"] = avg_relative_change_param(3.00, 4.50, "beta", ALPHA_G, N_G, "dP")
    rows["beta_300_450_dT"] = avg_relative_change_param(3.00, 4.50, "beta", ALPHA_G, N_G, "dT")
    # n 影响: Rth下降, dP增大(按alpha分档)
    rows["n_2_10_Rth"] = avg_relative_change_param(2, 10, "n", ALPHA_G, BETA_G, "Rth")
    rows["n_2_10_dP_by_alpha"] = {
        a: avg_relative_change_param(2, 10, "n", [a], BETA_G, "dP")
        for a in ALPHA_G
    }
    return rows


def avg_relative_change_param(v1, v2, which, grid_a, grid_b, out_col):
    """通用版:把 which('beta'或'n') 从v1变到v2,固定另外两个参数遍历grid_a x grid_b
    (which='n'时,grid_a是alpha取值,grid_b是beta取值)"""
    changes = []
    for a in grid_a:
        for b in grid_b:
            if which == "beta":
                alpha1, beta1, n1 = a, v1, b
                alpha2, beta2, n2 = a, v2, b
            else:  # which == "n"
                alpha1, beta1, n1 = a, b, v1
                alpha2, beta2, n2 = a, b, v2
            X = np.array([[alpha1, beta1, n1], [alpha2, beta2, n2]])
            X_std = scaler.transform(X)
            y = gprs[out_col].predict(X_std)
            changes.append((y[1] - y[0]) / y[0] * 100)
    return np.mean(changes)


# ---------- 1.3 alpha*拐点交叉验证(GPR直接求argmin,比半经验式更可信) ----------

def gpr_alpha_star(beta_grid=(3.0, 3.5, 4.0, 4.5), n_grid=(2, 4, 6, 8, 10), n_points=41):
    """在GPR(R2>0.999)上直接对alpha扫描求Rth平均值的argmin,作为alpha*的交叉验证"""
    alphas = np.linspace(0.10, 0.30, n_points)
    avg = []
    for a in alphas:
        vals = [gprs["Rth"].predict(scaler.transform([[a, b, n]]))[0]
                for b in beta_grid for n in n_grid]
        avg.append(np.mean(vals))
    avg = np.array(avg)
    i = np.argmin(avg)
    return alphas[i], avg[i]


# ---------- 1.4 机理关联式与数据一致性定量检验 ----------

def mechanism_data_agreement(dp_fit, rth_fit):
    """机理关联式(1.1标定)在样本上的平均相对偏差,作为6.1.2定量吻合指标"""
    return {
        "dp_mape_pct": dp_fit["mape"] * 100,
        "rth_mape_pct": rth_fit["mape"] * 100,
        "dp_r2": dp_fit["r2"],
        "rth_r2": rth_fit["r2"],
    }


def solve():
    dp_fit = fit_dp_corr(FINNED)
    rth_fit = fit_rth_corr(data)

    print("== 1.1 半经验关联式标定 ==")
    print(f"dP* = {dp_fit['C']:.4f} * beta^{dp_fit['a']:.4f} * (1-alpha)^{dp_fit['b']:.4f} * n^{dp_fit['c']:.4f}")
    print(f"  R2={dp_fit['r2']:.4f}  MAPE={dp_fit['mape']*100:.2f}%  (n>0的{len(FINNED)}个样本)")
    print(f"Rth* = {rth_fit['R0']:.4f} + {rth_fit['c1']:.4f}*(alpha-{rth_fit['alpha_star']:.4f})^2 "
          f"+ {rth_fit['c2']:.4f}*beta + {rth_fit['c3']:.4f}*n + {rth_fit['c4']:.4f}*alpha*n")
    print(f"  R2={rth_fit['r2']:.4f}  MAPE={rth_fit['mape']*100:.2f}%  (全部{len(data)}个样本)")

    print("\n== 1.2 影响幅度定量表(基于GPR代理模型,控制变量网格平均) ==")
    inf = influence_table()
    print(f"alpha 0.10->0.20: Rth平均变化 {inf['alpha_010_020_Rth']:.2f}%")
    print(f"alpha 0.20->0.30: Rth平均变化 {inf['alpha_020_030_Rth']:.2f}%")
    print(f"alpha 0.10->0.30: dP平均变化 {inf['alpha_010_030_dP']:.2f}%")
    print(f"beta  3.00->4.50: dP平均变化 {inf['beta_300_450_dP']:.2f}%")
    print(f"beta  3.00->4.50: dT平均变化 {inf['beta_300_450_dT']:.2f}%")
    print(f"n     2->10:      Rth平均变化 {inf['n_2_10_Rth']:.2f}%")
    print("n     2->10:      dP平均变化(按alpha分档):")
    for a, v in inf["n_2_10_dP_by_alpha"].items():
        print(f"    alpha={a}: {v:.2f}%")

    print("\n== 1.4 机理关联式与数据一致性(6.1.2定量吻合指标) ==")
    agree = mechanism_data_agreement(dp_fit, rth_fit)
    print(f"dP关联式: R2={agree['dp_r2']:.4f}  平均相对偏差={agree['dp_mape_pct']:.2f}%")
    print(f"Rth关联式: R2={agree['rth_r2']:.4f}  平均相对偏差={agree['rth_mape_pct']:.2f}%")
    print(f"alpha*(半经验式标定值) = {rth_fit['alpha_star']:.4f}")
    alpha_star_gpr, rth_at_star = gpr_alpha_star()
    print(f"alpha*(GPR交叉验证,argmin,更可信) = {alpha_star_gpr:.4f}  (对应Rth均值={rth_at_star:.4f};"
          f"论文预期在0.2附近,以此值为准)")

    out = {
        "dp_fit": dp_fit, "rth_fit": rth_fit,
        "influence": inf, "agreement": agree,
        "alpha_star_gpr": alpha_star_gpr,
    }
    jb.dump(out, common.DATA_DIR / "q1_result.pkl")
    return out


if __name__ == "__main__":
    solve()

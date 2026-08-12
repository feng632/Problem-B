import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common

import numpy as np
import joblib as jb
from scipy.stats import qmc
from SALib.sample import sobol as sobol_sample
from SALib.analyze import sobol as sobol_analyze

import solve_q3 as q3

res = jb.load(common.DATA_DIR / "gpr.pkl")
scaler = res["_scaler"]
outputs = ["Rth", "dP", "dT"]
gprs = {col: res[col]["gpr"] for col in outputs}

EPS = 0.05  # 综合扰动幅度 +-5%(eq:perturb)
N_MC = 8000  # LHS蒙特卡洛样本数,>=5000(FILL_CHECKLIST 5.1要求)

# 结构参数标称设计点:用问题三的综合最优方案 X* 作为标称点(其余分析都在此点展开)
q3_res = jb.load(common.DATA_DIR / "q3_result.pkl")
X0 = np.array(q3_res["x_star"])  # [alpha0, beta0, n0]

# 工况参数标称点(附件2采集时的固定工况,04-models.tex式(eq:perturb)前文)
MDOT0, TIN0, QV0 = 1.0, 293.0, 5e9  # g/s, K, W/m^3(仅用于表示相对扰动,不代入GPR)


def predict(X):
    return q3.predict(np.atleast_2d(X))


# ---------- 5.1 结构参数层(严格,GPR直接支撑) ----------

# Sobol/LSA/LHS用的结构参数域:取"有针肋"模式的连续box(x3当连续处理,
# 是GSA里对整数变量的常规近似,评估时不取整,因为这里研究的是"加工误差"
# 连续扰动,不是重新做整数设计搜索)
SOBOL_PROBLEM = {
    "num_vars": 3,
    "names": ["x1", "x2", "x3"],
    "bounds": [list(q3.X1_FINNED_BOUNDS), [3.00, 4.50], [2, 10]],
}


def sobol_indices(N=1024):
    """Sobol一阶主效应S_i与总效应S_Ti,对三个结构参数x1,x2,x3、三个输出分别给出"""
    param_values = sobol_sample.sample(SOBOL_PROBLEM, N)
    result = {}
    for col in outputs:
        X_std = scaler.transform(param_values)
        Y = gprs[col].predict(X_std)
        Si = sobol_analyze.analyze(SOBOL_PROBLEM, Y, print_to_console=False)
        result[col] = {"S1": Si["S1"], "ST": Si["ST"]}
    return result


def lsa_structural(X0=X0, h_rel=1e-3):
    """局部归一化敏感性系数 S_ij^local = dGj/dxi * xi0/yj0,中心差分(eq:lsa)"""
    F0 = predict(X0)[0]
    S = np.zeros((3, 3))  # 行=x1,x2,x3  列=Rth,dP,dT
    for i in range(3):
        h = max(abs(X0[i]) * h_rel, 1e-4)
        Xp, Xm = X0.copy(), X0.copy()
        Xp[i] += h
        Xm[i] -= h
        Fp = predict(Xp)[0]
        Fm = predict(Xm)[0]
        dF = (Fp - Fm) / (2 * h)
        S[i] = dF * X0[i] / F0
    return S  # S[i,j]


def lhs_montecarlo(X0=X0, eps=EPS, N=N_MC, seed=676767):
    """结构参数层LHS蒙特卡洛不确定性传播(eq:perturb, sigma_zi=eps*zi0/3)"""
    sigma = eps * np.abs(X0) / 3
    sampler = qmc.LatinHypercube(d=3, seed=seed)
    U = sampler.random(N)  # (N,3) in [0,1)
    from scipy.stats import norm
    Z = norm.ppf(U)  # 标准正态分位数
    samples = X0 + Z * sigma
    F = predict(samples)  # (N,3): Rth,dP,dT
    F0 = predict(X0)[0]
    cv = F.std(axis=0, ddof=1) / F.mean(axis=0)
    p95 = np.quantile(F, 0.95, axis=0)
    y_limit = 1.10 * F0
    p_fail = (F > y_limit).mean(axis=0)
    return {"F0": F0, "cv": cv, "p95": p95, "y_limit": y_limit, "p_fail": p_fail, "F_samples": F}


# ---------- 5.2 工况参数层(近似,线性化,eq:op-linear) ----------
#
# GPR从未在mdot/T_in/q_v三个维度上训练过(附件2数据全部在固定标称工况下采集),
# 所以论文里"S_ij^local由代理模型梯度有限差分近似"这句话对工况参数层literally
# 是算不出来的——这是main分支论文文本里遗留的一处表述和可执行性之间的缺口。
# 这里改用基于05-models.tex 5.5.1节(1)已经建立的无量纲化结果(Re,Pr主导)
# 做一阶物理标度估算,不是GPR梯度,推导依据见下方注释,结果需要论文手确认
# 措辞是否要改成"基于机理标度关系近似"而不是"代理模型梯度"。
#
# 推导:
#  - mdot: 固定几何下 Re∝mdot。层流微通道热入口段常用关联式 Nu~Re^(1/3)Pr^(1/3)
#    (Leveque型),h∝Nu,故 Rth*∝1/h∝mdot^(-1/3) => S=-1/3;dT*的驱动机制与
#    对流换热同源,近似取同一量级 S=-1/3。
#    压降(层流Poiseuille,f=64/Re∝1/mdot,原始ΔP∝f*mdot^2∝mdot;
#    无量纲化分母rho*U^2∝mdot^2,故dP*∝mdot^-1)=> S=-1。
#  - T_in: 无量纲温度以Delta T_ref(与T_in相关的参考温差)归一化,一阶展开下
#    T_in的直接贡献被归一化过程抵消,只剩物性随温度变化的二阶效应,取S约等于0。
#  - q_v: 对流-传导线性问题中,ΔT_ref通常正比于q_v,Rth*=ΔT_actual/ΔT_ref、
#    dT*同理,分子分母同比例缩放,一阶抵消,S约等于0;dP*是纯流体力学量,
#    与发热功率解耦,S=0。
OP_SENSITIVITY = {
    #        Rth     dP      dT
    "mdot": {"Rth": -1 / 3, "dP": -1.0, "dT": -1 / 3},
    "Tin":  {"Rth": 0.0,    "dP": 0.0,  "dT": 0.0},
    "qv":   {"Rth": 0.0,    "dP": 0.0,  "dT": 0.0},
}


def op_linear_impact(eps=EPS):
    """工况参数+-eps扰动下,按eq:op-linear线性叠加估算三项指标的相对变化幅度"""
    impact = {}
    for col in outputs:
        s = OP_SENSITIVITY["mdot"][col] * eps + OP_SENSITIVITY["Tin"][col] * eps + OP_SENSITIVITY["qv"][col] * eps
        impact[col] = s  # 三个工况参数同向拉满+eps的最坏情形线性叠加(相对变化量)
    return impact


# ---------- 5.3 验证闭环对比表(tab:q5-compare) ----------

def verification_closure(eps=EPS, N=N_MC):
    """X*(问题三)与X_robust(问题四)分别过结构层MC + 工况层线性叠加,对比CV/Pfail"""
    q4_res = jb.load(common.DATA_DIR / "q4_result.pkl")
    X_star = np.array(q3_res["x_star"])
    X_robust = np.array(q4_res["x_robust"])

    op_impact = op_linear_impact(eps)  # {col: relative shift}
    # 工况层线性叠加是确定性的均值平移,不改变结构MC样本的绝对标准差,
    # 只平移均值:合成CV_j = std(结构MC样本)/(mean(结构MC样本)*(1+工况线性偏移))

    rows = {}
    for name, X in [("X_star", X_star), ("X_robust", X_robust)]:
        mc = lhs_montecarlo(X0=X, eps=eps, N=N)
        op_shift = np.array([op_impact[col] for col in outputs])
        mean_combined = mc["F0"] * (1 + op_shift)
        std_struct = mc["cv"] * mc["F0"]
        cv_combined = std_struct / mean_combined
        y_limit = 1.10 * mc["F0"]
        p_fail_combined = (mc["F_samples"] * (1 + op_shift) > y_limit).mean(axis=0)
        rows[name] = {
            "X": X, "F0": mc["F0"],
            "cv": cv_combined, "p_fail": p_fail_combined,
            "meets_cv": bool((cv_combined < 0.03).all()),
            "meets_pfail": bool((p_fail_combined < 1e-3).all()),
        }
    return rows


def solve():
    print(f"标称点 X0(=Q3综合最优X*) = alpha={X0[0]:.4f} beta={X0[1]:.2f} n={X0[2]:.4f}")

    print("\n== 5.1(1) 局部归一化敏感性系数 S_ij^local(结构参数,标称点X0) ==")
    S_lsa = lsa_structural()
    for i, name in enumerate(["x1(alpha)", "x2(beta)", "x3(n)"]):
        print(f"  {name}: Rth={S_lsa[i,0]:+.4f}  dP={S_lsa[i,1]:+.4f}  dT={S_lsa[i,2]:+.4f}")

    print("\n== 5.1(2) Sobol全局敏感性指数(结构参数x1,x2,x3) ==")
    sobol_res = sobol_indices(N=1024)
    for col in outputs:
        S1 = sobol_res[col]["S1"]
        ST = sobol_res[col]["ST"]
        print(f"  {col}: S1(x1,x2,x3)={np.round(S1,4)}  ST(x1,x2,x3)={np.round(ST,4)}")

    print(f"\n== 5.1(3) LHS蒙特卡洛不确定性传播(N={N_MC}, eps={EPS*100:.0f}%,结构层X0=X*) ==")
    mc = lhs_montecarlo()
    for j, col in enumerate(outputs):
        print(f"  {col}: y0={mc['F0'][j]:.4f}  CV={mc['cv'][j]*100:.4f}%  "
              f"P95={mc['p95'][j]:.4f}  y_limit={mc['y_limit'][j]:.4f}  Pfail={mc['p_fail'][j]*100:.4f}%")

    print("\n== 5.2 工况参数层线性化影响(近似,基于机理标度关系,非GPR梯度——详见代码注释) ==")
    op_impact = op_linear_impact()
    for col in outputs:
        print(f"  {col}: +{EPS*100:.0f}%综合工况扰动 -> 相对变化 {op_impact[col]*100:+.2f}%")

    print("\n== 5.3 验证闭环对比表(tab:q5-compare) ==")
    closure = verification_closure()
    for name, row in closure.items():
        cv_pct = row["cv"] * 100
        pfail_max = row["p_fail"].max()
        print(f"  {name}: X={np.round(row['X'],4)}")
        print(f"    CV1={cv_pct[0]:.4f}% CV2={cv_pct[1]:.4f}% CV3={cv_pct[2]:.4f}%  "
              f"Pfail(max over 3)={pfail_max*100:.4f}%  "
              f"CV<3%达标={row['meets_cv']}  Pfail~=0达标={row['meets_pfail']}")

    # ---- 5.4/6.2 最敏感参数结论(取Sobol总效应ST在3个输出上的最大值判定) ----
    ST_matrix = np.array([sobol_res[col]["ST"] for col in outputs])  # (3out, 3param)
    flat_idx = np.unravel_index(np.argmax(ST_matrix), ST_matrix.shape)
    most_sensitive_param = ["x1(alpha,针肋宽度比)", "x2(beta,歧管深高比)", "x3(n,针肋排数)"][flat_idx[1]]
    most_sensitive_output = outputs[flat_idx[0]]
    print(f"\n== 5.4/6.2 结论 ==")
    print(f"最敏感参数-指标组合: {most_sensitive_output} 对 {most_sensitive_param} 的扰动最敏感 "
          f"(ST={ST_matrix[flat_idx]:.4f})")
    strong_params = []
    for pi, pname in enumerate(["x1", "x2", "x3"]):
        if (ST_matrix[:, pi] > 0.2).any():
            strong_params.append(pname)
    print(f"强敏感参数(存在某指标ST>0.2): {strong_params if strong_params else '无'}")

    out = {
        "X0": X0, "S_lsa": S_lsa, "sobol": sobol_res, "mc": mc,
        "op_impact": op_impact, "closure": closure,
        "most_sensitive_param": most_sensitive_param,
        "most_sensitive_output": most_sensitive_output,
        "strong_params": strong_params,
    }
    jb.dump(out, common.DATA_DIR / "q5_result.pkl")
    return out


if __name__ == "__main__":
    solve()

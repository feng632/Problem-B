import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import matplotlib.pyplot as plt
import common
import joblib as jb

res = jb.load(common.DATA_DIR / "gpr.pkl")
scaler = res["_scaler"]
gpr_rth = res["Rth"]["gpr"]
gpr_dp = res["dP"]["gpr"]

ALPHAS = np.linspace(0.10, 0.30, 41)
BETA_FIXED = 3.75  # 中位数附近的代表值
N_LEVELS = [2, 4, 6, 8, 10]

fig, axes = plt.subplots(1, 2, figsize=(13, 5))

# 左图: alpha-Rth 曲线族(不同n),标注拐点
ax = axes[0]
avg_curve = np.zeros_like(ALPHAS)
for n in N_LEVELS:
    X = np.column_stack([ALPHAS, np.full_like(ALPHAS, BETA_FIXED), np.full_like(ALPHAS, n)])
    y = gpr_rth.predict(scaler.transform(X))
    avg_curve += y
    ax.plot(ALPHAS, y, marker="", label=f"n={n}")
avg_curve /= len(N_LEVELS)
i_star = np.argmin(avg_curve)
alpha_star = ALPHAS[i_star]
ax.axvline(alpha_star, linestyle="--", color="grey")
ax.annotate(f"α*≈{alpha_star:.2f}", (alpha_star, avg_curve[i_star]),
            textcoords="offset points", xytext=(8, 8))
ax.set_xlabel("针肋宽度比 α")
ax.set_ylabel("无量纲热阻 $R_{th}^*$")
ax.set_title(f"α-$R_{{th}}^*$ 曲线族 (β={BETA_FIXED})")
ax.legend(fontsize=8)

# 右图: alpha-dP 曲线族(不同n),验证总体正相关
ax = axes[1]
for n in N_LEVELS:
    X = np.column_stack([ALPHAS, np.full_like(ALPHAS, BETA_FIXED), np.full_like(ALPHAS, n)])
    y = gpr_dp.predict(scaler.transform(X))
    ax.plot(ALPHAS, y, marker="", label=f"n={n}")
ax.set_xlabel("针肋宽度比 α")
ax.set_ylabel("无量纲压降 $\\Delta P^*$")
ax.set_title(f"α-$\\Delta P^*$ 曲线族 (β={BETA_FIXED})")
ax.legend(fontsize=8)

common.savefig("fig_q1.png")

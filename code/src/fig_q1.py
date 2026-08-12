import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
import common
import joblib as jb

res = jb.load(common.DATA_DIR / "gpr.pkl")
scaler = res["_scaler"]
gpr_rth = res["Rth"]["gpr"]
gpr_dp = res["dP"]["gpr"]

ALPHAS = np.linspace(0.10, 0.30, 81)
BETA_FIXED = 3.75  # 歧管深高比取值中点的代表值
N_LEVELS = [2, 4, 6, 8, 10]

# n 为有序变量,用 viridis(感知均匀、色盲安全)的 5 档渐变色编码排数递增
N_COLORS = [cm.viridis(0.15 + 0.7 * i / (len(N_LEVELS) - 1)) for i in range(len(N_LEVELS))]

fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.8))

# ---------- 左图: alpha-Rth 曲线族,标注拐点 ----------
ax = axes[0]
avg_curve = np.zeros_like(ALPHAS)
for n, c in zip(N_LEVELS, N_COLORS):
    X = np.column_stack([ALPHAS, np.full_like(ALPHAS, BETA_FIXED), np.full_like(ALPHAS, n)])
    y = gpr_rth.predict(scaler.transform(X))
    avg_curve += y
    ax.plot(ALPHAS, y, color=c, lw=1.8, label=f"$n={n}$")
avg_curve /= len(N_LEVELS)

# 拐点:对曲线族平均求 argmin 并标注(该 β 处的拐点区域,与论文全局交叉验证值 α*≈0.2 一致)
i_star = np.argmin(avg_curve)
alpha_star = ALPHAS[i_star]
ax.axvline(alpha_star, linestyle="--", color="gray", lw=1.2)
ax.annotate(
    f"拐点区域 $\\alpha\\approx{alpha_star:.2f}$",
    xy=(alpha_star, avg_curve[i_star]), xycoords="data",
    xytext=(alpha_star + 0.028, avg_curve[i_star] + 0.006), textcoords="data",
    arrowprops=dict(arrowstyle="->", color="gray", lw=1.0),
    fontsize=10, color="dimgray",
)
ax.set_xlabel(r"针肋宽度比 $\alpha$")
ax.set_ylabel(r"无量纲热阻 $R_{th}^*$")
ax.set_title(f"(a) $\\alpha$–$R_{{th}}^*$ 曲线族($\\beta={BETA_FIXED}$)")
ax.legend(fontsize=8, ncol=5, loc="upper center", frameon=False,
          bbox_to_anchor=(0.5, -0.13))
ax.set_ylim(0.72, 0.775)

# ---------- 右图: alpha-dP 曲线族 ----------
ax = axes[1]
for n, c in zip(N_LEVELS, N_COLORS):
    X = np.column_stack([ALPHAS, np.full_like(ALPHAS, BETA_FIXED), np.full_like(ALPHAS, n)])
    y = gpr_dp.predict(scaler.transform(X))
    ax.plot(ALPHAS, y, color=c, lw=1.8, label=f"$n={n}$")
ax.set_xlabel(r"针肋宽度比 $\alpha$")
ax.set_ylabel(r"无量纲压降 $\Delta P^*$")
ax.set_title(f"(b) $\\alpha$–$\\Delta P^*$ 曲线族($\\beta={BETA_FIXED}$)")
ax.legend(fontsize=8, ncol=5, loc="upper center", frameon=False,
          bbox_to_anchor=(0.5, -0.13))

fig.tight_layout()
common.savefig("fig_q1.png")

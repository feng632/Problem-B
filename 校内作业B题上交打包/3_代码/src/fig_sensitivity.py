import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import matplotlib.pyplot as plt
import common
import joblib as jb

res = jb.load(common.DATA_DIR / "q5_result.pkl")
sobol = res["sobol"]
S_lsa = res["S_lsa"]
closure = res["closure"]

outputs = ["Rth", "dP", "dT"]
param_names = [r"$x_1$ ($\alpha$)", r"$x_2$ ($\beta$)", r"$x_3$ ($n$)"]
param_short = ["x1", "x2", "x3"]
out_labels = [r"$R_{th}^*$", r"$\Delta P^*$", r"$\Delta T^*$"]

# 指标 → 颜色语义(与 fig_q2 一致):Rth=蓝 dP=橙 dT=绿
OUT_COLOR = [common.COLOR_RTH, common.COLOR_DP, common.COLOR_DT]
OUT_EDGE = ["#00517A", "#8A3A00", "#006B52"]  # 同色系深色描边,柱状更有层次

fig, axes = plt.subplots(2, 2, figsize=(13, 8.6))

# ---------- (a) Sobol 总效应指数:分组柱状 ----------
ax = axes[0, 0]
x = np.arange(len(param_names))
width = 0.25
for j, col in enumerate(outputs):
    ST = sobol[col]["ST"]
    bars = ax.bar(x + j * width, ST, width, label=out_labels[j],
                  color=OUT_COLOR[j], edgecolor=OUT_EDGE[j], lw=0.6, zorder=3)
    for b in bars:  # 柱顶数值标注
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.012,
                f"{b.get_height():.2f}", ha="center", va="bottom",
                fontsize=7.5, color="dimgray")
ax.axhline(0.2, linestyle="--", color="gray", lw=1.0, zorder=2)
ax.text(2.62, 0.215, "ST = 0.2", fontsize=8, color="gray", ha="right")
ax.set_xticks(x + width)
ax.set_xticklabels(param_names)
ax.set_ylabel("Sobol 总效应指数 $S_{Ti}$")
ax.set_ylim(0, 0.85)
ax.set_title("(a) Sobol 全局敏感性总效应指数")
ax.legend(fontsize=8, frameon=False, loc="upper left")

# ---------- (b) 局部归一化敏感性系数 LSA:热力图(原折线违反"离散点不连折线") ----------
ax = axes[0, 1]
im = ax.imshow(S_lsa, cmap="RdBu_r", vmin=-0.9, vmax=0.9, aspect="auto")
ax.set_xticks(range(3))
ax.set_xticklabels(out_labels)
ax.set_yticks(range(3))
ax.set_yticklabels(param_names)
# 单元格数值标注:正负号+两位小数,深底用白字
for i in range(3):
    for j in range(3):
        v = S_lsa[i, j]
        text_color = "white" if abs(v) > 0.55 else "black"
        ax.text(j, i, f"{v:+.2f}", ha="center", va="center",
                fontsize=9.5, color=text_color)
ax.set_title("(b) 局部归一化敏感性系数 $S_{ij}^{local}$(标称点 $X^*$)")
cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
cbar.set_label(r"$S_{ij}^{local} = \partial G_j/\partial x_i \cdot x_i^0/y_j^0$",
               fontsize=9)

# ---------- (c) ±5% 扰动变异系数对比:分组柱状 + 阈值线 ----------
ax = axes[1, 0]
X_star_cv = closure["X_star"]["cv"] * 100
X_robust_cv = closure["X_robust"]["cv"] * 100
x = np.arange(len(outputs))
width = 0.35
b1 = ax.bar(x - width / 2, X_star_cv, width, label=r"综合最优 $X^*$",
            color=common.COLOR_RTH, edgecolor="#00517A", lw=0.6, zorder=3)
b2 = ax.bar(x + width / 2, X_robust_cv, width, label=r"鲁棒方案 $X_{robust}$",
            color=common.COLOR_DP, edgecolor="#8A3A00", lw=0.6, zorder=3)
for bars in (b1, b2):
    for b in bars:
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.03,
                f"{b.get_height():.2f}", ha="center", va="bottom",
                fontsize=8, color="dimgray")
ax.axhline(3.0, linestyle="--", color="gray", lw=1.0, zorder=2)
ax.text(2.4, 3.08, "CV = 3% 阈值", fontsize=8, color="gray", ha="right")
ax.set_xticks(x)
ax.set_xticklabels(out_labels)
ax.set_ylabel("变异系数 CV (%)")
ax.set_ylim(0, 3.6)
ax.set_title("(c) ±5% 扰动下变异系数对比(含工况线性叠加)")
ax.legend(fontsize=8, frameon=False, loc="upper left")

# ---------- (d) ΔT 的一阶 vs 总效应:分组柱状 ----------
ax = axes[1, 1]
col = "dT"
S1 = sobol[col]["S1"]
ST = sobol[col]["ST"]
x = np.arange(len(param_names))
b1 = ax.bar(x - width / 2, S1, width, label=r"一阶主效应 $S_i$",
            color="#56B4E9", edgecolor="#1E7DB8", lw=0.6, zorder=3)
b2 = ax.bar(x + width / 2, ST, width, label=r"总效应 $S_{Ti}$",
            color=common.COLOR_RTH, edgecolor="#00517A", lw=0.6, zorder=3)
for bars in (b1, b2):
    for b in bars:
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.012,
                f"{b.get_height():.2f}", ha="center", va="bottom",
                fontsize=7.5, color="dimgray")
ax.set_xticks(x)
ax.set_xticklabels(param_names)
ax.set_ylabel("Sobol 指数")
ax.set_ylim(0, 0.85)
ax.set_title(r"(d) $\Delta T^*$ 的一阶主效应与总效应对比")
ax.legend(fontsize=8, frameon=False, loc="upper left")

fig.tight_layout()
common.savefig("fig_sensitivity.png")

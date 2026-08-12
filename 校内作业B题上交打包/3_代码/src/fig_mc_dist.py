import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde
import common
import joblib as jb

res = jb.load(common.DATA_DIR / "q5_result.pkl")
mc = res["mc"]
F_samples = mc["F_samples"]   # (8000, 3)
F0 = mc["F0"]                 # 标称值
p95 = mc["p95"]               # 95% 分位数
y_limit = mc["y_limit"]       # 越界阈值 1.10*F0
cv = mc["cv"]
p_fail = mc["p_fail"]

outputs = ["Rth", "dP", "dT"]
OUT_LABEL = [r"$R_{th}^*$", r"$\Delta P^*$", r"$\Delta T^*$"]
OUT_COLOR = [common.COLOR_RTH, common.COLOR_DP, common.COLOR_DT]

fig, axes = plt.subplots(1, 3, figsize=(14, 4.2))

for j, (ax, col, lab, color) in enumerate(zip(axes, outputs, OUT_LABEL, OUT_COLOR)):
    x = F_samples[:, j]
    # 直方图 + KDE 密度曲线
    n_bins = 60
    ax.hist(x, bins=n_bins, density=True, color=color, alpha=0.45,
            edgecolor="white", linewidth=0.4, zorder=2)
    kde = gaussian_kde(x)
    xs = np.linspace(x.min(), x.max(), 300)
    ax.plot(xs, kde(xs), color=color, lw=2.0, zorder=3)

    # 竖线:标称值 / P95(越界阈值 1.10y0 远在分布尾部之外,面板右侧用箭头示意)
    ax.axvline(F0[j], color="black", lw=1.2, zorder=4)
    ax.axvline(p95[j], color="gray", linestyle=":", lw=1.4, zorder=4)

    # 数值标注
    ax.text(0.03, 0.95, f"CV = {cv[j]*100:.2f}%\n$P_{{fail}}$ = {p_fail[j]*100:.2f}%",
            transform=ax.transAxes, va="top", ha="left", fontsize=9,
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="lightgray", alpha=0.85))
    # 越界阈值箭头提示(线在可视范围外,用右缘箭头表示)
    ax.annotate(
        r"越界阈值 $1.10y_0$ →",
        xy=(0.995, 0.60), xycoords="axes fraction",
        xytext=(0.79, 0.97), textcoords="axes fraction",
        ha="right", va="top", fontsize=8, color=common.COLOR_DP,
        arrowprops=dict(arrowstyle="->", color=common.COLOR_DP, lw=1.0),
    )
    # 两条线的图例(右上)
    from matplotlib.lines import Line2D
    handles = [
        Line2D([0], [0], color="black", lw=1.2, label=r"标称值 $y_0$"),
        Line2D([0], [0], color="gray", lw=1.4, linestyle=":", label="$y_{P95}$"),
    ]
    ax.legend(handles=handles, fontsize=7.5, frameon=False, loc="upper right")

    ax.set_xlabel(lab)
    ax.set_ylabel("概率密度")
    ax.set_title(f"{lab}(±5% 扰动, $N=8000$)")
    ax.set_ylim(bottom=0)

fig.tight_layout()
common.savefig("fig_mc_dist.png")

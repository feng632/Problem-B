import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
import common
import joblib as jb

res = jb.load(common.DATA_DIR / "q3_result.pkl")
F_front = res["F_front"]
f_min = res["f_min"]
f_max = res["f_max"]
F_star = res["F_star"]

# 每个前沿解的归一化理想点距离(颜色编码:好解盆地)
F_norm = (F_front - f_min) / (f_max - f_min)
D = np.sqrt(np.sum(F_norm ** 2, axis=1) / 3)

PAIRS = [
    (0, 1, r"$R_{th}^*$", r"$\Delta P^*$", "(a) $R_{th}^*$–$\Delta P^*$ 投影"),
    (0, 2, r"$R_{th}^*$", r"$\Delta T^*$", "(b) $R_{th}^*$–$\Delta T^*$ 投影"),
    (1, 2, r"$\Delta P^*$", r"$\Delta T^*$", "(c) $\Delta P^*$–$\Delta T^*$ 投影"),
]

fig, axes = plt.subplots(1, 3, figsize=(14, 4.5))
sc = None
for ax, (i, j, xlab, ylab, title) in zip(axes, PAIRS):
    sc = ax.scatter(F_front[:, i], F_front[:, j], c=D, cmap="viridis",
                    s=10, alpha=0.55, linewidths=0, zorder=2)
    ax.scatter([F_star[i]], [F_star[j]], marker="*", s=260,
               color=common.COLOR_RTH, edgecolors="white",
               linewidths=1.0, zorder=4)
    ax.annotate(
        r"$\mathbf{F}^*$",
        xy=(F_star[i], F_star[j]), xycoords="data",
        xytext=(8, 12), textcoords="offset points",
        fontsize=11, color=common.COLOR_RTH,
        arrowprops=dict(arrowstyle="->", color=common.COLOR_RTH, lw=1.0),
    )
    ax.set_xlabel(xlab)
    ax.set_ylabel(ylab)
    ax.set_title(title)

cbar = fig.colorbar(sc, ax=axes, fraction=0.025, pad=0.02)
cbar.set_label("理想点距离 $D$", fontsize=9)
cbar.set_ticks([D.min(), (D.min() + D.max()) / 2, D.max()])
cbar.set_ticklabels([f"{D.min():.2f}(优)", f"{(D.min()+D.max())/2:.2f}", f"{D.max():.2f}(劣)"])

fig.tight_layout()
common.savefig("fig_pareto.png")

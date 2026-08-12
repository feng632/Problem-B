import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import matplotlib.pyplot as plt
import common
import joblib as jb
import solve_q3 as q3  # 复用 predict/normalize

res = jb.load(common.DATA_DIR / "q4_result.pkl")
max_regret = res["max_regret"]     # (2000,) 候选池各方案的最大后悔值
R_max = res["R_max"]               # minimax 最优后悔值(鲁棒方案)
epsilon = res["epsilon"]           # 容许上限
all_w = res["all_w"]
D_star_grid = res["D_star"]
f_min, f_max = res["f_min"], res["f_max"]
x_star = np.array(jb.load(common.DATA_DIR / "q3_result.pkl")["x_star"])  # 等权综合最优

# 计算等权综合最优 X* 在全偏好空间的最大后悔值(与候选池同口径)
F_xs = q3.predict(np.atleast_2d(x_star))[0]
F_norm = (F_xs - f_min) / (f_max - f_min)
regret_xs = np.sqrt(np.sum(all_w * F_norm ** 2, axis=1)) - D_star_grid
regret_xs_max = regret_xs.max()

fig, ax = plt.subplots(figsize=(8.5, 4.5))

# 直方图主区(x 从 0.20 起,让 ε 与直方图的量级差距直观可见)
ax.hist(max_regret, bins=45, color="#B8C4D0", edgecolor="white",
        linewidth=0.4, zorder=2)
ax.axvline(R_max, color=common.COLOR_DP, linestyle="--", lw=1.8, zorder=4)
ax.axvline(epsilon, color="gray", linestyle=":", lw=1.6, zorder=4)
ax.axvline(regret_xs_max, color=common.COLOR_RTH, linestyle="-.", lw=1.6, zorder=4)

# R_max 标注(箭头从右上文字指向线)
ax.annotate(
    f"$R_{{max}}={R_max:.4f}$\n(鲁棒方案)",
    xy=(R_max, 0.02), xycoords=("data", "axes fraction"),
    xytext=(0.34, 0.86), textcoords=("axes fraction", "axes fraction"),
    fontsize=9.5, color=common.COLOR_DP, ha="center",
    arrowprops=dict(arrowstyle="->", color=common.COLOR_DP, lw=1.1),
)
# X* 后悔值标注
ax.annotate(
    f"$R^{{max}}(\\mathbf{{X}}^*)={regret_xs_max:.4f}$\n(等权综合最优)",
    xy=(regret_xs_max, 0.02), xycoords=("data", "axes fraction"),
    xytext=(0.86, 0.86), textcoords=("axes fraction", "axes fraction"),
    fontsize=9.5, color=common.COLOR_RTH, ha="center",
    arrowprops=dict(arrowstyle="->", color=common.COLOR_RTH, lw=1.1),
)
# ε 标注(线在左缘,文字放左上,箭头指向左缘)
ax.annotate(
    f"容许上限 $\\epsilon={epsilon:.4f}$",
    xy=(epsilon, 0.30), xycoords=("data", "axes fraction"),
    xytext=(0.02, 0.94), textcoords=("axes fraction", "axes fraction"),
    fontsize=9.5, color="dimgray", ha="left",
    arrowprops=dict(arrowstyle="->", color="gray", lw=1.1),
)

ax.set_xlabel("候选方案的最大后悔值 $R^{max}(\\mathbf{X})$")
ax.set_ylabel("候选方案数(共 2000 个)")
ax.set_title("候选池最大后悔值分布与鲁棒方案位置")
ax.set_xlim(0, max_regret.max() * 1.03)

fig.tight_layout()
common.savefig("fig_regret.png")

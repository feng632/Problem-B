import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
import common
import joblib as jb

res = jb.load(common.DATA_DIR / "q4_result.pkl")
all_w = res["all_w"]          # (31, 3) 权重单纯形采样点
X_star = res["X_star"]        # (31, 3) 各权重下的最优解
D_star = res["D_star"]        # (31,)
scenario_w = res["scenario_w"]
scenario_names = res["scenario_names"]

# 重心坐标 → 等边三角形平面投影(无额外依赖)
def simplex_xy(w):
    return w[:, 0] + 0.5 * w[:, 2], w[:, 2] * np.sqrt(3) / 2

# 三角形三个顶点(w1=1, w2=1, w3=1)与边线
def draw_triangle(ax):
    verts_w = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]], dtype=float)
    xs, ys = simplex_xy(verts_w)
    for k in range(3):
        ax.plot([xs[k], xs[(k + 1) % 3]], [ys[k], ys[(k + 1) % 3]],
                color="gray", lw=1.2, zorder=1)
    # 顶点标签(放在三角形外侧)
    offset = [(0.0, -0.075), (0.0, -0.075), (0.13, 0.02)]
    labels = [r"$w_1$=1(散热)", r"$w_2$=1(泵功)", r"$w_3$=1(均匀性)"]
    for (x, y), lab, (dx, dy) in zip(zip(xs, ys), labels, offset):
        ax.text(x + dx, y + dy, lab, ha="center", va="top", fontsize=9, color="dimgray")

px, py = simplex_xy(all_w)
n_opt = X_star[:, 2]  # 各权重下的最优排数

fig, axes = plt.subplots(1, 2, figsize=(12.5, 5.2))

# ---------- (a) 偏好空间内最优排数的分区结构 ----------
ax = axes[0]
draw_triangle(ax)
levels = sorted(set(n_opt.astype(int)))
cmap = cm.viridis
norm_n = plt.Normalize(min(levels) - 0.5, max(levels) + 0.5)
sc = ax.scatter(px, py, c=n_opt, cmap=cmap, norm=norm_n, s=95,
                edgecolors="white", linewidths=0.8, zorder=3)
# 三个典型场景点 + 等权点
sx, sy = simplex_xy(scenario_w)
ax.scatter(sx, sy, marker="s", s=110, facecolors="none",
           edgecolors=common.COLOR_RTH, linewidths=1.6, zorder=4)
eq_x, eq_y = simplex_xy(np.array([[1/3, 1/3, 1/3]]))
ax.scatter(eq_x, eq_y, marker="D", s=90, facecolors="none",
           edgecolors=common.COLOR_DP, linewidths=1.6, zorder=4)
ax.text(eq_x[0] + 0.02, eq_y[0] - 0.055, "等权点", fontsize=8,
        color=common.COLOR_DP, ha="left")
for (x, y), name in zip(zip(sx, sy), scenario_names):
    ax.text(x + 0.015, y, name, fontsize=7.5, color=common.COLOR_RTH, ha="left")
cbar = fig.colorbar(sc, ax=ax, fraction=0.046, pad=0.04,
                    ticks=levels)
cbar.set_label("最优针肋排数 $n^*$", fontsize=9)
ax.set_aspect("equal")
ax.axis("off")
ax.set_title("(a) 偏好空间内最优排数分区")

# ---------- (b) D*(W) 在偏好空间的光滑变化 ----------
ax = axes[1]
draw_triangle(ax)
D_zero = np.where(D_star < 1e-6, np.nan, D_star)  # 顶点处 D*=0(单目标退化),置 NaN 保持色标有意义
sc = ax.scatter(px, py, c=D_zero, cmap="viridis", s=95,
                edgecolors="white", linewidths=0.8, zorder=3)
ax.scatter(sx, sy, marker="s", s=110, facecolors="none",
           edgecolors=common.COLOR_RTH, linewidths=1.6, zorder=4)
ax.scatter(eq_x, eq_y, marker="D", s=90, facecolors="none",
           edgecolors=common.COLOR_DP, linewidths=1.6, zorder=4)
cbar = fig.colorbar(sc, ax=ax, fraction=0.046, pad=0.04)
cbar.set_label(r"综合距离 $D^*(\mathbf{W})$", fontsize=9)
ax.set_aspect("equal")
ax.axis("off")
ax.set_title("(b) $D^*(\\mathbf{W})$ 在偏好空间的光滑变化")

fig.tight_layout()
common.savefig("fig_weight_sweep.png")

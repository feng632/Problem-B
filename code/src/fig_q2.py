import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import matplotlib.pyplot as plt
import common
import joblib as jb

res = jb.load(common.DATA_DIR / "gpr.pkl")
outputs = [k for k in res.keys() if not k.startswith("_")]

# 指标 → 颜色语义:Rth=蓝 dP=橙 dT=绿(Okabe-Ito 色盲安全)
OUT_COLOR = {
    "Rth": common.COLOR_RTH,
    "dP": common.COLOR_DP,
    "dT": common.COLOR_DT,
}
OUT_LABEL = {
    "Rth": r"$R_{th}^*$",
    "dP": r"$\Delta P^*$",
    "dT": r"$\Delta T^*$",
}

fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.3))

for col, ax in zip(outputs, axes):
    y_true = res[col]["y_true"]
    y_pred = res[col]["y_pred"]
    r2 = res[col]["r2"]
    rmse = res[col]["rmse"]

    ax.scatter(y_pred, y_true, s=26, alpha=0.75, edgecolors="white",
               linewidths=0.5, color=OUT_COLOR[col], zorder=3)
    ax.axline((0, 0), slope=1, linestyle="--", color="gray", lw=1.0, zorder=2)

    # 拟合精度标注(左上角,数据点集中在右上,不冲突)
    ax.text(0.04, 0.94,
            f"$R^2={r2:.4f}$\nRMSE$={rmse:.2e}$",
            transform=ax.transAxes, va="top", ha="left",
            fontsize=9, bbox=dict(boxstyle="round,pad=0.3",
                                  fc="white", ec="lightgray", alpha=0.85))

    ax.set_title(f"{OUT_LABEL[col]}")
    ax.set_xlabel("GPR 预测值")
    ax.set_ylabel("真实值(CFD)")
    ax.set_aspect("equal")
    lo = min(y_true.min(), y_pred.min())
    hi = max(y_true.max(), y_pred.max())
    pad = (hi - lo) * 0.12
    ax.set_xlim(lo - pad, hi + pad)
    ax.set_ylim(lo - pad, hi + pad)
    # 只保留少数刻度,避免数字堆叠
    ax.ticklabel_format(style="plain", useOffset=False)
    ax.set_xticks(np.round(np.linspace(lo, hi, 4), 3))
    ax.set_yticks(np.round(np.linspace(lo, hi, 4), 3))

fig.tight_layout()
common.savefig("fig_q2_true_pred.png")

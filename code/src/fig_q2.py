import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib.pyplot as plt
import common
import joblib as jb

res = jb.load(common.DATA_DIR / "gpr.pkl")
outputs = [k for k in res.keys() if not k.startswith("_")]
fig, axes = plt.subplots(1, 3, figsize=(15, 5))

for col, ax in zip(outputs, axes):
    ax.scatter(res[col]["y_pred"], res[col]["y_true"])
    ax.axline((0, 0), slope=1, linestyle="--", color="grey")
    ax.set_title(f"{col}")
    ax.set_xlabel("预测值")
    ax.set_ylabel("真实值")
    ax.set_aspect("equal")
    lo = min(res[col]["y_true"].min(), res[col]["y_pred"].min())
    hi = max(res[col]["y_true"].max(), res[col]["y_pred"].max())
    pad = (hi - lo) * 0.1
    ax.set_xlim(lo - pad, hi + pad)
    ax.set_ylim(lo - pad, hi + pad)

common.savefig("fig_q2_true_pred.png")
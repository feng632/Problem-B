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
param_names = ["x1(α)", "x2(β)", "x3(n)"]

fig, axes = plt.subplots(2, 2, figsize=(14, 11))

# (a) Sobol total-effect indices
ax = axes[0, 0]
x = np.arange(len(param_names))
width = 0.25
for j, col in enumerate(outputs):
    ST = sobol[col]["ST"]
    ax.bar(x + j * width, ST, width, label=col)
ax.set_xticks(x + width)
ax.set_xticklabels(param_names)
ax.set_ylabel("Sobol total-effect $S_{Ti}$")
ax.set_title("(a) Sobol全局敏感性总效应指数")
ax.legend(fontsize=8)
ax.axhline(0.2, linestyle="--", color="grey", alpha=0.5)
ax.annotate("ST=0.2 threshold", (2.5, 0.21), fontsize=7, color="grey")

# (b) LSA structural coefficients
ax = axes[0, 1]
for i, pname in enumerate(param_names):
    ax.plot(outputs, S_lsa[i], "o-", label=pname)
ax.axhline(0, linestyle="--", color="grey")
ax.set_ylabel("$S_{ij}^{local}$")
ax.set_title("(b) 局部归一化敏感性系数(标称点X*)")
ax.legend(fontsize=8)

# (c) MC uncertainty propagation: CV bars
ax = axes[1, 0]
X_star_cv = closure["X_star"]["cv"] * 100
X_robust_cv = closure["X_robust"]["cv"] * 100
x = np.arange(len(outputs))
width = 0.35
ax.bar(x - width / 2, X_star_cv, width, label="综合最优X*")
ax.bar(x + width / 2, X_robust_cv, width, label="鲁棒方案X_robust")
ax.set_xticks(x)
ax.set_xticklabels(outputs)
ax.set_ylabel("CV (%)")
ax.set_title("(c) ±5%扰动下变异系数对比(含工况线性叠加)")
ax.legend(fontsize=8)
ax.axhline(3.0, linestyle="--", color="grey", alpha=0.5)
ax.annotate("CV=3% threshold", (1.5, 3.1), fontsize=7, color="grey")

# (d) Sobol first-order vs total-effect comparison (dT only, most sensitive)
ax = axes[1, 1]
col = "dT"
S1 = sobol[col]["S1"]
ST = sobol[col]["ST"]
x = np.arange(len(param_names))
width = 0.35
ax.bar(x - width / 2, S1, width, label="一阶主效应 $S_i$")
ax.bar(x + width / 2, ST, width, label="总效应 $S_{Ti}$")
ax.set_xticks(x)
ax.set_xticklabels(param_names)
ax.set_ylabel("Sobol index")
ax.set_title("(d) ΔT Sobol指数(一阶vs总效应)")
ax.legend(fontsize=8)

fig.tight_layout()
common.savefig("fig_sensitivity.png")

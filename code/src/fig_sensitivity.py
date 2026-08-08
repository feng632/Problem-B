# =====================================================================
#  fig_sensitivity.py — 灵敏度分析占位图(论文 06-sensitivity.tex 引用)
#  比赛开始后:替换为真实的灵敏度分析图(参数扰动对性能的影响)
# =====================================================================
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common
import numpy as np
import matplotlib.pyplot as plt

# ---- 占位内容:替换为真实数据 ----
x = np.linspace(0, 10, 100)
y = np.cos(x)

fig, ax = plt.subplots()
ax.plot(x, y)
ax.set_xlabel("参数扰动幅度")
ax.set_ylabel("性能指标变化率")
ax.set_title("灵敏度分析(占位图)")

common.savefig("fig_sensitivity.png")

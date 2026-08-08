# =====================================================================
#  fig_q1.py — 问题1 结果占位图(论文 05-solution.tex 引用)
#  比赛开始后:替换为真实的问题1 结果图(参数影响规律等)
# =====================================================================
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common
import numpy as np
import matplotlib.pyplot as plt

# ---- 占位内容:替换为真实数据 ----
x = np.linspace(0, 10, 100)
y = np.sin(x)

fig, ax = plt.subplots()
ax.plot(x, y)
ax.set_xlabel("参数")
ax.set_ylabel("热阻 R_th")
ax.set_title("问题1 结果(占位图)")

common.savefig("fig_q1.png")

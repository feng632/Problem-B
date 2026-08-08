# =====================================================================
#  fig_example.py — 画图脚本示例(模板)
#
#  规则:
#   1. 画图脚本统一命名为 *_fig.py,make fig 会自动运行所有 *_fig.py
#   2. 脚本开头 import common 即可获得路径与统一样式
#   3. 用 common.savefig() 保存,make fig 会自动同步到 paper/figures/
#   4. 不要 print 大量调试信息;最终提交的图要能复现
#
#  示例:读取 code/data/ 下的数据画一张图。
# =====================================================================
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # 保证能 import common
import common
import matplotlib.pyplot as plt

import numpy as np

# ---- 读数据(按实际数据格式调整) ----
# df = pd.read_excel(common.DATA_DIR / "附件.xlsx")

# ---- 画图 ----
x = np.linspace(0, 10, 100)
y = np.sin(x) + 0.1 * x

fig, ax = plt.subplots()
ax.plot(x, y, label="示例曲线")
ax.set_xlabel("x")
ax.set_ylabel("y")
ax.legend()
ax.set_title("示例图")

common.savefig("fig_example.png")

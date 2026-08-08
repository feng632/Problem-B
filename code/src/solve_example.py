# =====================================================================
#  solve_example.py — 求解脚本模板
#
#  规则:
#   1. 求解脚本命名为 solve_*.py,与画图脚本(_fig.py)区分开,
#      这样 make fig 只会跑画图,不会重复计算模型。
#   2. 从命令行运行:cd code && python src/solve_example.py
#   3. 最终结果(表格/数值)手工誊入论文 sections/05-solution.tex,
#      不要把临时结果文件提交到 git。
# =====================================================================
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common
import numpy as np

# ---- 读数据 ----
# df = pd.read_excel(common.DATA_DIR / "附件.xlsx")
# print(df.head())

# ---- 建模求解 ----
# 示例:求解一个线性规划
def solve_demo():
    return {"score": 42.0, "method": "demo"}

if __name__ == "__main__":
    result = solve_demo()
    print(result)

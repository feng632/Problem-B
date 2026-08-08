# =====================================================================
#  common.py — 公共配置:路径、matplotlib 样式、通用工具
#
#  所有脚本都以 code/ 为当前工作目录运行(make fig 保证),
#  统一从这里取路径,不要自己拼相对路径。
# =====================================================================
from pathlib import Path

# 路径
CODE_DIR = Path(__file__).resolve().parent.parent  # code/
DATA_DIR = CODE_DIR / "data"                       # code/data/
FIG_DIR = CODE_DIR / "figures"                     # code/figures/ (输出目录)

FIG_DIR.mkdir(exist_ok=True)

# ---------- matplotlib 全局样式(统一图风格,避免每人一版) ----------
import matplotlib

matplotlib.use("Agg")  # 服务器/无界面环境也能出图

import matplotlib.pyplot as plt

plt.rcParams.update({
    "font.family": "SimHei",            # Windows 中文字体;Linux 无此字体时改为 Noto Sans CJK SC
    "axes.unicode_minus": False,        # 解决负号显示为方块的问题
    "figure.dpi": 150,                  # 出图清晰度(国赛要求 300dpi 打印,提交前调高重跑)
    "savefig.dpi": 150,
    "figure.figsize": (8, 5),
    "axes.grid": True,
    "grid.alpha": 0.4,
})


def savefig(name: str) -> Path:
    """保存图片到 code/figures/,make fig 会自动同步到 paper/figures/。

    命名规范:fig_<内容>.png,例如 fig_q1.png、fig_sensitivity.png
    """
    path = FIG_DIR / name
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    print(f"[fig] saved -> {path}")
    return path

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
from matplotlib import font_manager

# 中文字体优先级:Noto Sans CJK SC > Noto Sans SC > Source Han Sans SC > SimHei > Microsoft YaHei
# 取第一个系统已安装的字体,找不到才用默认(此时中文会显示方框)
_FONT_CANDIDATES = [
    "Noto Sans CJK SC", "Noto Sans SC", "Source Han Sans SC",
    "Source Han Sans CN", "SimHei", "Microsoft YaHei",
]
_installed = {f.name for f in font_manager.fontManager.ttflist}
_zh_font = next((f for f in _FONT_CANDIDATES if f in _installed), None)

plt.rcParams.update({
    "font.family": _zh_font if _zh_font else "sans-serif",  # 中文字体
    "axes.unicode_minus": False,        # 解决负号显示为方块的问题
    "figure.dpi": 150,                  # 出图清晰度(国赛要求 300dpi 打印,提交前调高重跑)
    "savefig.dpi": 300,                 # 论文印刷 300 dpi
    "figure.figsize": (8, 5),
    "axes.grid": True,
    "grid.alpha": 0.3,
    "grid.linewidth": 0.6,
    "axes.linewidth": 0.8,              # 坐标轴线略细,出版级观感
    "axes.titlesize": 12,
    "axes.labelsize": 11,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 9,
    "legend.framealpha": 0.9,
    "lines.linewidth": 1.6,
})

# Okabe-Ito 色盲安全配色(统一全项目用色,避免每人一版颜色)
# 语义约定:
#   指标:Rth=蓝 dP=橙 dT=绿
#   结构参数:x1(α)=蓝 x2(β)=橙 x3(n)=绿
#   方案对比:X*=蓝 X_robust=橙
OKABE_ITO = ["#0072B2", "#D55E00", "#009E73", "#CC79A7",
             "#E69F00", "#56B4E9", "#F0E442", "#000000"]
COLOR_RTH, COLOR_DP, COLOR_DT = OKABE_ITO[0], OKABE_ITO[1], OKABE_ITO[2]


def savefig(name: str) -> Path:
    """保存图片到 code/figures/,make fig 会自动同步到 paper/figures/。

    命名规范:fig_<内容>.png,例如 fig_q1.png、fig_sensitivity.png
    """
    path = FIG_DIR / name
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    print(f"[fig] saved -> {path}")
    return path

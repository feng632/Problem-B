# =====================================================================
#  Problem-B 数学建模竞赛仓库
#  全国大学生数学建模竞赛(国赛)团队协作仓库
#  本仓库用于管理:论文(LaTeX)、代码(Python)、数据、提交物
#
#  ▶ 三人如何配合:见 [COLLABORATION.md](COLLABORATION.md)(建模手/论文手/代码手分工)
#
#  本次赛题:B题 高性能芯片热管理系统优化
#  - 问题1:机理建模(结构参数 → 热阻/压降/温度非均匀性)
#  - 问题2:代理模型(附件2 样本数据)
#  - 问题3:多目标优化 → 综合最优设计方案
#  - 问题4:指标权重变化 → 鲁棒设计方案
#  - 问题5:参数扰动 → 敏感性分析
#  结构参数:针肋宽度比 / 歧管深高比 / 针肋排数
#  附件:附件1(结构参数)、附件2(样本数据)→ 放 code/data/
# =====================================================================

## 目录结构

```
Problem-B/
├── Makefile            # 团队协作核心:一键出图/编译/打包
├── paper/              # 论文主目录(国赛 cumcmthesis 模板已合入)
│   ├── main.tex        # 论文主文件(结构/摘要/团队信息)
│   ├── cumcmthesis.cls # 国赛官方模板类文件(一般不改)
│   ├── sections/       # 分节内容(队员各写一节,避免冲突)
│   ├── figures/        # 论文引用图(代码生成的图自动同步到这里)
│   └── refs.bib        # 参考文献(如使用 biblatex)
├── code/               # 建模代码
│   ├── src/            # 脚本:common.py 公共配置、*_fig.py 画图、solve_*.py 求解
│   ├── data/           # 数据(不提交 git,自行从官网下载)
│   └── requirements.txt
├── data/               # (可选)数据副本
├── scripts/            # 工具脚本:MD5 计算、重命名等
├── templates/          # 队友上传模板的临时区(已合入 paper/,这里仅作参考)
├── submission/         # 提交物:论文 PDF、支撑材料 zip、MD5 码(全部自动生成)
└── .gitignore
```

## 快速开始(Windows)

**0. 准备环境**(只需要做一次):

```bash
# ① Git for Windows:https://git-scm.com/download/win(自带 git-bash)
# ② Python:https://www.python.org/downloads/ 安装后 pip 安装依赖:
py -3 -m pip install -r code/requirements.txt

# ③ LaTeX:推荐 TeX Live(https://tug.org/texlive/) 或 MiKTeX(https://miktex.org/)
#    必须能用 xelatex 编译中文(需 ctex 宏包)
# ④ make(Windows 需要单独装):
winget install ezwinports.make
```

**1. 克隆仓库并开工:**

```bash
git clone https://github.com/feng632/Problem-B.git
cd Problem-B

make data        # 查看数据说明(数据需自行从官网下载)
make fig         # 运行画图脚本,生成 code/figures 并同步到 paper/figures
make pdf         # 编译论文 -> paper/main.pdf
make all         # 一条龙:出图 -> 编译 -> 打包
make pack        # 打包支撑材料 submission/main.zip + 计算论文 MD5 码
make files       # 查看仓库文件清单
make clean       # 清理编译产物
```

> **Windows 说明:** 所有 `make` 命令请在 **git-bash** 中运行。
> `make` 需另行安装(见上);Python 命令统一用 `py -3`(Windows 的 `python` 可能
> 指向应用商店占位符,会报错)。Makefile 已内置这些处理。

## 协作约定

1. **论文分节写作**:每个队员负责 `paper/sections/` 中不同的节文件,避免 merge 冲突。
   改完某节后,`make pdf` 看整体效果。
2. **图由代码生成**:画图脚本一律命名为 `code/src/*_fig.py` 并输出到
   `code/figures/`,`make fig` 会自动同步到 `paper/figures/`。不要手动拷贝图片进
   paper/figures,避免互相覆盖。
3. **提交物自动生成**:论文 PDF、支撑材料 zip、MD5 码都在 `submission/` 由
   `make pack` 生成,**不要手工打包**。
4. **数据不提交**:原始数据自行从官网下载放入 `code/data/`;大文件不要 push。
5. **论文模板**:国赛官方 cumcmthesis 模板已合入 `paper/`。`templates/` 里的
   example.tex 是队友上传的模板参考,不要拿去编译提交。

## 提交流程(国赛)

1. `make all` —— 生成最新论文与支撑材料
2. 报名号命名的论文 PDF: `py -3 scripts/rename_to_prob.py <报名号>`
3. 在官网提交系统上传 `submission/<报名号>-B.pdf`,并上传支撑材料 `submission/main.zip`
4. 校验:提交时官网要求填写论文 MD5 码,即 `submission/main.md5` 中的值
   (由 `make pack` 自动计算)

## 本机环境检查

```bash
make -v        # make 是否可用
py -3 -V       # Python 版本
xelatex -v     # LaTeX 是否安装(无则不能 make pdf)
```

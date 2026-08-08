# =====================================================================
#  Problem-B 数学建模竞赛仓库
#  全国大学生数学建模竞赛(国赛)团队协作仓库
#  本仓库用于管理:论文(LaTeX)、代码(Python)、数据、提交物
# =====================================================================

## 目录结构

```
Problem-B/
├── Makefile            # 团队协作核心:一键出图/编译/打包
├── paper/              # 论文主目录
│   ├── main.tex        # 论文主文件(摘要、结构、引用)
│   ├── sections/       # 分节内容(队员各写一节,避免冲突)
│   ├── figures/        # 论文引用图(代码生成的图自动同步到这里)
│   └── refs.bib        # 参考文献(如使用 biblatex)
├── code/               # 建模代码
│   ├── src/            # 脚本:common.py 公共配置、*_fig.py 画图、solve_*.py 求解
│   ├── data/           # 数据(不提交 git,自行从官网下载)
│   └── requirements.txt
├── data/               # (可选)数据副本
├── scripts/            # 工具脚本:MD5 计算、重命名等
├── submission/         # 提交物:论文 PDF、支撑材料 zip、MD5 码(全部自动生成)
└── .gitignore
```

## 快速开始

```bash
# 1. 安装依赖(Windows:请用 Anaconda 或 pip;git-bash 已内置 make)
make data        # 查看数据说明(数据需自行从官网下载)
make fig         # 运行画图脚本,生成 code/figures 并同步到 paper/figures
make pdf         # 编译论文 -> paper/main.pdf
make all         # 一条龙:出图 -> 编译 -> 打包
make pack        # 打包支撑材料 submission/main.zip + 计算论文 MD5 码
make files       # 查看仓库文件清单
make clean       # 清理编译产物
```

> **Windows 说明:** 本仓库的 Makefile 假定使用 **git-bash** 环境。
> 安装 [Git for Windows](https://git-scm.com/download/win) 后,在仓库根目录右键
> "Git Bash Here",即可运行 `make` 系列命令。若命令找不到,请确认 git-bash 的
> PATH 中包含 `/usr/bin`(默认包含)。

## 协作约定

1. **论文分节写作**:每个队员负责 `paper/sections/` 中不同的节文件,避免 merge 冲突。
   改完 `main.tex` 或某节后,再统一 `make pdf` 看效果。
2. **图由代码生成**:画图脚本一律命名为 `code/src/*_fig.py` 并输出到
   `code/figures/`,`make fig` 会自动同步到 `paper/figures/`。不要手动拷贝图片进
   paper/figures,避免互相覆盖。
3. **提交物自动生成**:论文 PDF、支撑材料 zip、MD5 码都在 `submission/` 由
   `make pack` 生成,**不要手工打包**。
4. **数据不提交**:原始数据自行从官网下载放入 `code/data/`;大文件不要 push。

## 提交流程(国赛)

1. `make all` —— 生成最新论文与支撑材料
2. 报名号命名的论文 PDF: `python scripts/rename_to_prob.py <报名号>`
3. 在官网提交系统上传 `submission/<报名号>-B.pdf`,并上传支撑材料 `submission/main.zip`
4. 校验:提交时官网要求填写论文 MD5 码,即 `submission/main.md5` 中的值
   (由 `make pack` 自动计算)

## 本机环境检查

```bash
make -v        # make 是否可用
python -V      # Python 版本
pdflatex -v    # LaTeX 是否安装(无则不能 make pdf,Windows 推荐 TeX Live)
```

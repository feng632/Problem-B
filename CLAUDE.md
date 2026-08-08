# CLAUDE.md — 本仓库协作说明(给 Claude Code 会话)

数学建模竞赛(国赛,Problem-B)团队仓库,LaTeX + Python。

## 环境
- Windows + git-bash。Shell 命令走 bash 语法,`make` 可用。
- 项目非 git 仓库的现状已规划,`git init` 后由 git 管理。

## 常用命令(必须在仓库根目录运行)
- `make fig` — 运行 `code/src/*_fig.py`,图输出 `code/figures/` 并同步到 `paper/figures/`
- `make pdf` — latexmk -xelatex 编译 `paper/main.pdf`
- `make all` — fig → pdf → pack 一条龙
- `make pack` — 打包支撑材料 `submission/main.zip` + 计算论文 MD5(`submission/main.md5`)
- `make clean` — 清理编译产物

## 结构要点
- `paper/sections/` 按节拆分,队员各写一节,避免 merge 冲突
- 图片命名 `fig_<内容>.png`;代码生成的图走 `make fig`,不要手动拷入 paper/figures
- 原始数据放 `code/data/`,不提交 git
- 参考文献:thebibliography 手动编号(不依赖 biber)

## 注意事项
- 国赛正文限 20 页,注意篇幅
- 提交物(main.zip、main.md5、重命名 PDF)均由 make/scripts 生成,不要手工制作
- 若改 paper 文件名或结构,同步更新 Makefile 与 README

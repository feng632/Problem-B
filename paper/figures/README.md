# paper/figures 说明

本目录存放论文 `main.tex` 中引用的图。

**维护规则:**
- 由代码生成的图:在 `code/src/*_fig.py` 中生成,执行 `make fig` 后自动同步到本目录。**不要手动把图拷进本目录**,避免覆盖队友的图。
- 手绘/截图类图(流程图、示意图):直接放入本目录,命名遵循 `fig_<内容>.png`,并在提交信息中注明。
- 命名冲突时:后写入者需重命名自己的图,并在论文中同步修改 `\includegraphics` 引用。

**论文引用方式:**
```latex
\includegraphics[width=0.8\textwidth]{figures/fig_q1.png}
```
（路径相对于 `paper/main.tex`）

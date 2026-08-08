# templates/ 上传区

本目录用于**队友上传模板文件**(论文模板、封面、样式文件等),全队共用。

> **当前状态:** 国赛官方 cumcmthesis 模板(example.tex + cumcmthesis.cls)
> **已合入 `paper/` 并验证编译通过**,现在仓库的正式论文以此为准。
> 本目录里的 example.tex 保留作参考,不要再改动/提交模板。

**如果还有新模板要上传:**

1. **网页拖拽**(推荐,不需要 git):打开仓库主页 → `Add file` → `Upload files` → 把模板文件拖进网页 → `Commit changes`
   - 注意:网页不支持传文件夹,多个文件请逐个拖
2. **git 命令行**(标准做法):
   ```bash
   git clone https://github.com/feng632/Problem-B.git
   cd Problem-B/templates
   # 把模板文件放进来
   git add .
   git commit -m "上传模板:xxx"
   git push
   ```

**命名建议:**
```
templates/
├── 模板说明.md          ← 写清模板的用途、来源、使用方法
├── paper_template/      ← 完整论文模板(含 main.tex、样式文件、封面等)
└── ...
```

> 上传后请通知队长,由队长(或 Claude)把模板合并进 `paper/` 正式结构。
> 上传区只是临时存放,**不直接参与编译**。

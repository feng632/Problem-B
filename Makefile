# -*- makefile -*-
# =====================================================================
#  Problem-B - Math Modeling Contest - Team Collaboration Makefile
#
#  Usage: make <target>   (run at repo root)
#
#  Common targets:
#    make help     list all targets
#    make fig      run code/src/*_fig.py scripts -> code/figures + sync to paper/figures
#    make pdf      compile paper -> paper/main.pdf (xelatex)
#    make all      one-shot: fig -> pdf -> pack
#    make pack     build submission package (submission/*.zip) + paper MD5 code
#    make md5      recompute paper MD5 code only
#    make clean    remove build artifacts
#
#  Windows notes:
#    - Run in git-bash. Install make via: winget install ezwinports.make
#    - This file is pure ASCII on purpose: Windows make reads Makefiles
#      using the system code page (GBK), which garbles UTF-8 Chinese.
#      All user-facing messages are English to stay portable.
#    - Recipes run with bash (SHELL := /bin/bash).
# =====================================================================
SHELL       := /bin/bash

# ---------- paths (all targets run at repo root) ----------
P      := $(CURDIR)
PAPER  := $(P)/paper
CODE   := $(P)/code
SRC    := $(CODE)/src
FIGD   := $(CODE)/figures
PFIGD  := $(PAPER)/figures
SCRIPTS:= $(P)/scripts
DATA   := $(P)/data
SUBM   := $(P)/submission

# ---------- tools ----------
# Windows 下 python 命令可能是商店占位符(WindowsApps),用 py -3 启动真实解释器
PY           = py -3
PDF2PNG      = gs -dNOPAUSE -dBATCH -sDEVICE=png16m -r300 -sOutputFile=$@ $<

# ---------- LaTeX intermediate artifacts (removed by clean) ----------
LATEX_AUX := aux log out toc bbl blg fdb_latexmk fls synctex.gz xdv nav snm vrb

# ---------- figure scripts (code/src/*_fig.py) ----------
FIG_SCRIPTS := $(wildcard $(SRC)/*_fig.py)

# ---------- paper artifact ----------
PAPER_PDF := $(PAPER)/main.pdf

.PHONY: help fig data pdf pack md5 files all clean

.DEFAULT_GOAL := help

help:
	@echo 'Problem-B team collaboration Makefile'
	@echo '-------------------------------------'
	@echo '  make fig      run figure scripts -> code/figures, sync to paper/figures'
	@echo '  make pdf      compile paper -> paper/main.pdf'
	@echo '  make all      one-shot: fig -> pdf -> pack'
	@echo '  make pack     build submission/*.zip + paper MD5 code'
	@echo '  make md5      recompute paper MD5 code (submission/main.md5)'
	@echo '  make files    list repo files'
	@echo '  make clean    remove build artifacts'

# ---------- figures: run every *_fig.py, then sync to paper ----------
fig: $(FIG_SCRIPTS)
	@$(foreach f,$(FIG_SCRIPTS),cd $(CODE) && $(PY) $(f) &&) true
	@mkdir -p $(PFIGD)
	@cp -f $(FIGD)/* $(PFIGD)/ 2>/dev/null || true
	@echo "[fig] figures generated -> $(FIGD), synced to $(PFIGD)"

# ---------- data: remind to download from official site ----------
data:
	@echo "Download raw data from the contest official site into $(DATA)/"
	@echo "and update $(DATA)/README.md with its source."
	@echo "Data is NOT committed to git (see .gitignore); it is packed into the zip."

# ---------- paper: latexmk (xelatex) ----------
$(PAPER_PDF): $(wildcard $(PAPER)/*.tex) $(wildcard $(PAPER)/sections/*.tex)
	cd $(PAPER) && latexmk -xelatex -interaction=nonstopmode -halt-on-error main.tex
	@echo "[pdf] paper built -> $(PAPER_PDF)"

pdf: $(PAPER_PDF)

# ---------- pack: submission zip + paper MD5 code (GuoSai deliverables) ----------
# zip contents: paper/main.pdf + code/ + data/
# MD5 code is computed over the paper PDF itself (as required by the contest),
# NOT over the zip.
$(SUBM)/main.zip: $(PAPER_PDF)
	@echo "[pack] building submission package..."
	@mkdir -p $(SUBM)/_stage
	@rm -rf $(SUBM)/_stage/*
	@mkdir -p $(SUBM)/_stage/paper
	@cp $(PAPER_PDF) $(SUBM)/_stage/paper/
	@cp -r $(CODE) $(SUBM)/_stage/
	@cp -r $(DATA) $(SUBM)/_stage/
	@rm -rf $(SUBM)/_stage/code/__pycache__ $(SUBM)/_stage/code/*/__pycache__
	@cd $(SUBM)/_stage && rm -f paper/main.aux paper/main.log paper/main.out paper/main.bbl paper/main.blg
	@cd $(SUBM)/_stage && rm -f code/src/*.pyc
	@cd $(SUBM)/_stage && zip -qr ../main.zip .
	@rm -rf $(SUBM)/_stage
	@echo "[pack] submission package -> $(SUBM)/main.zip"

$(SUBM)/main.md5: $(PAPER_PDF)
	@$(PY) $(SCRIPTS)/md5_of.py $(PAPER_PDF) $(SUBM)/main.md5
	@echo "[md5] paper MD5 code -> $(SUBM)/main.md5"

pack: $(SUBM)/main.zip $(SUBM)/main.md5

md5: $(SUBM)/main.md5

# ---------- all: 一条龙 ----------
all: fig pdf pack

# ---------- misc ----------
files:
	@find $(P) -not -path '*/.git/*' -not -path '*/.claude/*' -not -path '*/__pycache__*' -type f | sed 's|^$(P)/||' | sort

clean:
	@rm -f $(foreach e,$(LATEX_AUX),$(PAPER)/main.$(e))
	@rm -f $(PAPER_PDF)
	@rm -f $(FIGD)/* $(PFIGD)/*
	@rm -rf $(SUBM)
	@echo "[clean] build artifacts removed"

# ---------- rule: paper/figures/foo.png from code/figures/foo.png ----------
$(PFIGD)/%.png: $(FIGD)/%.png
	$(PDF2PNG)

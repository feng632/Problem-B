import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

file = common.DATA_DIR / "data.xlsx"
data = pd.read_excel(file, header=1).rename(columns={
      "样本编号": "index",
      "针肋宽度比": "alpha",
      "歧管深高比": "beta",
      "单个歧管单元内沿流向的针肋排数": "n",
      "无量纲热阻": "Rth",
      "无量纲压降": "dP",
      "无量纲温度非均匀性": "dT",
  })
print(data.groupby(['beta','n'])['alpha'].nunique())
print(data.groupby(['alpha', 'n'])['beta'].nunique())
print(data.groupby(['alpha', 'beta'])['n'].nunique())


# 拆成 2x2 子图:每个子图固定一个 β,子图内部只画 n 这一个维度的 5 条线
# fig 还是只有一个(整张画布),ax 现在是一个 2x2 的数组,每个格子一个坐标系
fig, axes = plt.subplots(2, 2, figsize=(10, 7), sharex=True, sharey=True)
beta_values = sorted(data.loc[data["n"] != 0, "beta"].unique())

for beta_val, ax in zip(beta_values, axes.flat):   # axes.flat 把 2x2 拉平成4个,和4个β一一对应
    sub_beta = data[data["beta"] == beta_val]
    for n_val, sub in sub_beta.groupby("n"):
        if n_val == 0:
            continue
        sub = sub.sort_values("alpha")
        ax.plot(sub["alpha"], sub["Rth"], marker="o", label=f"n={n_val}")
    ax.set_title(f"β = {beta_val}")
    ax.legend(fontsize=7)   # 现在每个子图只有5条线,legend不用再压得很小

fig.supxlabel("针肋宽度比 α")   # 整张画布共用的坐标轴标签,不用每个子图重复写
fig.supylabel("无量纲热阻 R_th")
common.savefig("fig_q1_alpha_rth.png")

fig, axes = plt.subplots(2, 2, figsize=(10, 7), sharex=True, sharey=True)

for beta_val, ax in zip(beta_values, axes.flat):
    sub_beta = data[data["beta"] == beta_val]
    for n_val, sub in sub_beta.groupby("n"):
        if n_val == 0:
            continue
        sub = sub.sort_values("alpha")
        ax.plot(sub["alpha"], sub["dP"], marker="o", label=f"n={n_val}")
    ax.set_title(f"β = {beta_val}")
    ax.legend(fontsize=7)

fig.supxlabel("针肋宽度比 α")
fig.supylabel("无量纲压降 dP")
common.savefig("fig_q1_alpha_dP.png")

# 这里换了分面维度:按 alpha 分 4 个子图(排除 alpha=0,因为 n 只有一个取值),
# 子图内部画 n 这条线,x 轴变成 beta —— 和上面两张的“分面变量/线条变量”正好对调
alpha_values = sorted(data.loc[data["n"] != 0, "alpha"].unique())
fig, axes = plt.subplots(2, 2, figsize=(10, 7), sharex=True, sharey=True)

for alpha_val, ax in zip(alpha_values, axes.flat):
    sub_alpha = data[data["alpha"] == alpha_val]
    for n_val, sub in sub_alpha.groupby("n"):
        if n_val == 0:
            continue
        sub = sub.sort_values("beta")
        ax.plot(sub["beta"], sub["dT"], marker="o", label=f"n={n_val}")
    ax.set_title(f"α = {alpha_val}")
    ax.legend(fontsize=7)

fig.supxlabel("歧管深高比 β")
fig.supylabel("无量纲温度非均匀性 dT")
common.savefig("fig_q1_beta_dT.png")

fig, axes = plt.subplots(2, 2, figsize=(10, 7), sharex=True, sharey=True)
for alpha_val, ax in zip(alpha_values, axes.flat):
    sub_n = data[(data["alpha"] == alpha_val) & (data["n"] != 0)]
    for beta_val, sub in sub_n.groupby("beta"):
        sub = sub.sort_values("n")
        ax.plot(sub["n"], sub["dP"], marker="o", label=f"β={beta_val}")
    ax.set_title(f"α={alpha_val}")
    ax.legend(fontsize=7)

fig.supxlabel("单个歧管单元内沿流向的针肋排数 n")
fig.supylabel("无量纲压降 dP")
common.savefig("fig_q1_n_dP.png")
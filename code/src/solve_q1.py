import pandas as pd

file = r"../data/data.xlsx"
data = pd.read_excel(file, header=1).rename(columns={
      "样本编号": "index",
      "针肋宽度比": "alpha",
      "歧管深高比": "beta",
      "单个歧管单元内沿流向的针肋排数": "n",
      "无量纲热阻": "Rth",
      "无量纲压降": "dP",
      "无量纲温度非均匀性": "dT",
  })

print(data.columns.tolist())



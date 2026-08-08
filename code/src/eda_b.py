import pandas as pd

data = pd.read_excel('data.xlsx', header=1)

print("=== 数据形状 ===")
print(data.shape)

print("\n=== 列名 ===")
print(data.columns)

print("\n=== 前5行 ===")
print(data.head())

print("\n=== 各列数据类型 ===")
print(data.dtypes)

print("\n=== 输入列取值(验证网格设计) ===")
cases = 1
for col in data.columns[1:4]:
    vals = sorted(data[col].unique())
    print(f"{col}: {len(vals)}档 -> {vals}")
    cases *= len(vals)
print(f"理论网格数: {cases}, 实际样本数: {data.shape[0]}, 差: {cases - data.shape[0]}")

print("\n=== Pearson相关系数 ===")
corr_mat = data[data.columns[1:]].corr().round(3)
print(corr_mat)

print("\n=== 各输出列性质 ===")
print(data[data.columns[4:]].describe().round(4))

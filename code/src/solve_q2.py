import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common
import numpy as np
import pandas as pd
import sklearn as sk

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
inputs = ["alpha", "beta", "n"]
outputs = ["Rth", "dP", "dT"]


def gpr():
    X_raw = data[inputs]



if __name__ == "__main__":
    gpr()
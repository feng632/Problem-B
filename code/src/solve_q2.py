import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common
import numpy as np
import pandas as pd
import joblib as jb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.gaussian_process.kernels import WhiteKernel, RBF, ConstantKernel
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_percentage_error


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
    #每次选中一个输出维度进行训练,先进行总的一次切分,后续单独训练
    X_train, X_test, y_train, y_test = train_test_split(data[inputs], data[outputs], test_size=0.2, random_state=676767)

    # Z-score-scaler
    scaler = StandardScaler()
    X_train_std = scaler.fit_transform(X_train)
    X_test_std = scaler.transform(X_test)

    #kernel
    kernel = ConstantKernel(1.0, (1e-10, 1e10)) * RBF([1.0, 1.0, 1.0], (1e-10, 1e10)) + WhiteKernel(1.0, (1e-10, 1e10))

    #GPR
    result = {}
    for y_train_select_col in outputs:
        y_train_select = y_train[y_train_select_col]
        gpr = GaussianProcessRegressor(kernel=kernel, alpha=1e-8, normalize_y=True, n_restarts_optimizer=10)
        gpr.fit(X_train_std, y_train_select)
        mu, sigma = gpr.predict(X_test_std, return_std=True)

        result[y_train_select_col] = {
            "gpr": gpr,
            "y_true": y_test[y_train_select_col].to_numpy(),
            "y_pred": mu,
            "y_std": sigma,
            "r2": r2_score(y_test[y_train_select_col], mu),
            "rmse": mean_squared_error(y_test[y_train_select_col], mu) ** 0.5,
            "mape": mean_absolute_percentage_error(y_test[y_train_select_col], mu),
        }
        #保存GPR模型文件
    jb.dump(result, common.DATA_DIR / "gpr.pkl")
    print("duplicated data: ", data.duplicated(subset=inputs).sum(), "\n")
    for col, r in result.items():
        print(f"{col}: r2={r['r2']:.8f} rmse={r['rmse']:.8f} mape={r['mape']:.8f}")
    return result

if __name__ == "__main__":
    gpr()
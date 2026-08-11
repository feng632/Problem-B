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

        # 提取MLE寻优后的核超参数 theta*=[sigma_f, l1,l2,l3, sigma_n](eq:kernel,04-models.tex:264待回填)
        k_const_rbf, k_white = gpr.kernel_.k1, gpr.kernel_.k2
        sigma_f = np.sqrt(k_const_rbf.k1.constant_value)
        length_scales = k_const_rbf.k2.length_scale  # [l1, l2, l3] 对应 alpha, beta, n
        sigma_n = np.sqrt(k_white.noise_level)

        result[y_train_select_col] = {
            "gpr": gpr,
            "y_true": y_test[y_train_select_col].to_numpy(),
            "y_pred": mu,
            "y_std": sigma,
            "r2": r2_score(y_test[y_train_select_col], mu),
            "rmse": mean_squared_error(y_test[y_train_select_col], mu) ** 0.5,
            "mape": mean_absolute_percentage_error(y_test[y_train_select_col], mu),
            "theta_star": {"sigma_f": sigma_f, "length_scales": length_scales, "sigma_n": sigma_n},
        }
        #保存GPR模型文件(连同scaler一起,Q3要用同一套标准化)
    result["_scaler"] = scaler
    result["_input_cols"] = inputs
    jb.dump(result, common.DATA_DIR / "gpr.pkl")
    print("duplicated data: ", data.duplicated(subset=inputs).sum(), "\n")
    for col in outputs:
        r = result[col]
        print(f"{col}: r2={r['r2']:.8f} rmse={r['rmse']:.8f} mape={r['mape']:.8f}")
    print("\n== GPR最优超参数 theta*=[sigma_f, l_alpha, l_beta, l_n, sigma_n] ==")
    for col in outputs:
        t = result[col]["theta_star"]
        l1, l2, l3 = t["length_scales"]
        print(f"{col}: sigma_f={t['sigma_f']:.4f}  l_alpha={l1:.4f}  l_beta={l2:.4f}  l_n={l3:.4f}  "
              f"sigma_n={t['sigma_n']:.6f}")
    return result

if __name__ == "__main__":
    gpr()
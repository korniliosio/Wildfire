import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.metrics import average_precision_score
import time

SPLIT_DIR = "thesis_data/model_table/splits"

train_df = pd.read_parquet(f"{SPLIT_DIR}/train.parquet")
val_df   = pd.read_parquet(f"{SPLIT_DIR}/val.parquet")

drop_cols = ["fire_tomorrow", "fire", "date", "year", "cell_id"]

X_train = train_df.drop(columns=drop_cols)
y_train = train_df["fire_tomorrow"]

X_val = val_df.drop(columns=drop_cols)
y_val = val_df["fire_tomorrow"]

# imbalance weight from TRAIN ONLY
n_pos = y_train.sum()
n_neg = len(y_train) - n_pos
spw = n_neg / n_pos

dtrain = xgb.DMatrix(X_train, label=y_train)
dval   = xgb.DMatrix(X_val,   label=y_val)

def recall_precision_at_k(y_true, y_prob, k_frac=0.01):
    n = len(y_true)
    k = int(np.ceil(k_frac * n))
    order = np.argsort(-y_prob)
    top = y_true.iloc[order[:k]]
    recall = top.sum() / y_true.sum()
    precision = top.mean()
    return float(recall), float(precision)

def sample_params(rng):
    # log-uniform helper
    def logu(a, b):
        return float(np.exp(rng.uniform(np.log(a), np.log(b))))

    return {
        "objective": "binary:logistic",
        "eval_metric": "aucpr",
        "tree_method": "hist",
        "eta": logu(0.02, 0.2),
        "max_depth": int(rng.integers(3, 9)),              # 3..8
        "min_child_weight": logu(5, 300),                 # big helps rare events
        "subsample": float(rng.uniform(0.6, 1.0)),
        "colsample_bytree": float(rng.uniform(0.6, 1.0)),
        "gamma": logu(1e-4, 5.0),
        "reg_lambda": logu(0.5, 50.0),
        "reg_alpha": logu(1e-6, 5.0),
        "scale_pos_weight": float(spw),
        "verbosity": 0,
        "nthread": -1,
    }

def run_trial(params, num_boost_round=1500, early_stopping_rounds=50):
    model = xgb.train(
        params=params,
        dtrain=dtrain,
        num_boost_round=num_boost_round,
        evals=[(dtrain, "train"), (dval, "val")],
        early_stopping_rounds=early_stopping_rounds,
        verbose_eval=False
    )
    p_val = model.predict(dval)
    prauc = float(average_precision_score(y_val, p_val))
    r1, p1 = recall_precision_at_k(y_val, p_val, 0.01)
    best_iter = int(model.best_iteration)
    return prauc, r1, p1, best_iter

rng = np.random.default_rng(42)
results = []
N_TRIALS = 80  # increase to 150+ if you want

t0 = time.time()
best = (-1, None)

for i in range(N_TRIALS):
    params = sample_params(rng)
    prauc, r1, p1, best_iter = run_trial(params)
    row = {
        "trial": i,
        "val_prauc": prauc,
        "val_recall_at_1pct": r1,
        "val_precision_at_1pct": p1,
        "best_iteration": best_iter,
        **params
    }
    results.append(row)

    if prauc > best[0]:
        best = (prauc, row)

    if (i + 1) % 10 == 0:
        print(f"[{i+1}/{N_TRIALS}] best val PR-AUC so far: {best[0]:.6f}")

res_df = pd.DataFrame(results).sort_values("val_prauc", ascending=False)
out_path = "thesis_data/model/tuning/xgb_random_search_results.csv"
import os
os.makedirs(os.path.dirname(out_path), exist_ok=True)
res_df.to_csv(out_path, index=False)

print("\nSaved:", out_path)
print("\nTop 10 configs:")
print(res_df[["trial","val_prauc","val_recall_at_1pct","val_precision_at_1pct","best_iteration",
              "eta","max_depth","min_child_weight","subsample","colsample_bytree",
              "gamma","reg_lambda","reg_alpha"]].head(10).to_string(index=False))

import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.metrics import average_precision_score, roc_auc_score
import pandas as pd

# ----------------------------
# Load splits
# ----------------------------
SPLIT_DIR = "thesis_data/model_table/splits"

train_df = pd.read_parquet(f"{SPLIT_DIR}/train.parquet")
val_df   = pd.read_parquet(f"{SPLIT_DIR}/val.parquet")
test_df  = pd.read_parquet(f"{SPLIT_DIR}/test.parquet")

# ----------------------------
# Prepare data
# ----------------------------
drop_cols = ["fire_tomorrow", "fire", "date", "year", "cell_id"]

X_train = train_df.drop(columns=drop_cols)
y_train = train_df["fire_tomorrow"]

X_val = val_df.drop(columns=drop_cols)
y_val = val_df["fire_tomorrow"]

X_test = test_df.drop(columns=drop_cols)
y_test = test_df["fire_tomorrow"]

# ----------------------------
# Handle class imbalance
# ----------------------------
n_pos = y_train.sum()
n_neg = len(y_train) - n_pos
scale_pos_weight = n_neg / n_pos

print(f"scale_pos_weight = {scale_pos_weight:.1f}")

# ----------------------------
# DMatrix (XGBoost internal format)
# ----------------------------
dtrain = xgb.DMatrix(X_train, label=y_train)
dval   = xgb.DMatrix(X_val,   label=y_val)
dtest  = xgb.DMatrix(X_test,  label=y_test)

# ----------------------------
# Parameters
# ----------------------------
params = {
    "objective": "binary:logistic",
    "eval_metric": "aucpr",
    "tree_method": "hist",
    "eta": 0.0746,
    "max_depth": 8,
    "min_child_weight": 35,
    "subsample": 0.71,
    "colsample_bytree": 0.73,
    "gamma": 0.028,
    "reg_lambda": 3.77,
    "reg_alpha": 1e-6,
    "scale_pos_weight": scale_pos_weight,
    "nthread": -1,
    "verbosity": 0,
}



# ----------------------------
# Train with early stopping
# ----------------------------
evals = [(dtrain, "train"), (dval, "val")]

model = xgb.train(
    params=params,
    dtrain=dtrain,
    num_boost_round=500,
    evals=evals,
    early_stopping_rounds=50,
    verbose_eval=50,
)

model.save_model("thesis_data/model/xgb.model")

# Get gain-based importance
importance = model.get_score(importance_type="gain")

imp_df = (
    pd.DataFrame({
        "feature": importance.keys(),
        "gain": importance.values(),
    })
    .sort_values("gain", ascending=False)
)

# Normalize for readability (optional but recommended)
imp_df["gain_norm"] = imp_df["gain"] / imp_df["gain"].sum()

print("\nTop 15 features by gain:")
print(imp_df.head(15).to_string(index=False))

# Save for later plotting / thesis figures
out_path = "thesis_data/model/results/xgb_feature_importance_gain.csv"
import os
os.makedirs(os.path.dirname(out_path), exist_ok=True)
imp_df.to_csv(out_path, index=False)
print("\nSaved feature importance to:", out_path)

# ----------------------------
# Predict
# ----------------------------
p_val  = model.predict(dval)
p_test = model.predict(dtest)


def top_k_metrics(y_true, y_prob, k_frac):
    n = len(y_true)
    k = int(np.ceil(k_frac * n))

    order = np.argsort(-y_prob)
    top_idx = order[:k]

    y_top = y_true.iloc[top_idx]

    recall = y_top.sum() / y_true.sum()
    precision = y_top.mean()

    return recall, precision


def evaluate_top_k(y, p, name):
    print(f"\n{name} — Top-K metrics")
    print("-" * (len(name) + 15))
    for k in [0.001, 0.005, 0.01, 0.02, 0.05]:
        recall, precision = top_k_metrics(y, p, k)
        print(
            f"Top {k*100:4.1f}% | "
            f"Recall: {recall:6.3f} | "
            f"Precision: {precision:7.4f}"
        )


# Evaluate
evaluate_top_k(y_val,  p_val,  "Validation")
evaluate_top_k(y_test, p_test, "Test")


# ----------------------------
# Evaluation
# ----------------------------
def evaluate(y, p, name):
    print(f"\n{name}")
    print("-" * len(name))
    print("PR-AUC: ", average_precision_score(y, p))
    print("ROC-AUC:", roc_auc_score(y, p))

evaluate(y_val,  p_val,  "Validation")
evaluate(y_test, p_test, "Test")

import pandas as pd
import numpy as np
import random
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    average_precision_score,
    roc_auc_score,
    brier_score_loss,
)

SPLIT_DIR = "thesis_data/model_table/splits"

train_df = pd.read_parquet(f"{SPLIT_DIR}/train.parquet")
val_df   = pd.read_parquet(f"{SPLIT_DIR}/val.parquet")
test_df  = pd.read_parquet(f"{SPLIT_DIR}/test.parquet")

# Target

TARGET_COL = "fire_tomorrow"
y_train = train_df[TARGET_COL]
y_val   = val_df[TARGET_COL]
y_test  = test_df[TARGET_COL]

# Features
DROP_COLS = [
    "fire_tomorrow",
    "fire",
    "date",
    "year",
    "cell_id",
]

x_train = train_df.drop(columns=DROP_COLS)
x_val   = val_df.drop(columns=DROP_COLS)
x_test  = test_df.drop(columns=DROP_COLS)

# Model pipeline

pipe = Pipeline([
    ("scaler", StandardScaler()),
    ("logreg", LogisticRegression(
        max_iter=1000,
        class_weight="balanced",
        n_jobs=-1,
        solver="lbfgs",
    )),
])

# Train
pipe.fit(x_train, y_train)

# Predict
y_train_pred = pipe.predict_proba(x_train)[:, 1]
y_val_pred   = pipe.predict_proba(x_val)[:, 1]
y_test_pred  = pipe.predict_proba(x_test)[:, 1]

# Evaluate

coef = pipe.named_steps["logreg"].coef_[0]
features = x_train.columns

coef_df = (
    pd.DataFrame({"feature": features, "coef": coef})
    .sort_values("coef", key=np.abs, ascending=False)
)

# Top positive coefficients (increase fire risk): filter positives and sort descending
pos_df = coef_df[coef_df["coef"] > 0].sort_values("coef", ascending=False)
print("\nTop positive coefficients (increase fire risk):")
if not pos_df.empty:
    print(pos_df.head(10).to_string(index=False))
else:
    print("None")

# Top negative coefficients (decrease fire risk): filter negatives and sort ascending (most negative first)
neg_df = coef_df[coef_df["coef"] < 0].sort_values("coef", ascending=True)
print("\nTop negative coefficients (decrease fire risk):")
if not neg_df.empty:
    print(neg_df.head(10).to_string(index=False))
else:
    print("None")


def evaluate(y, p, name):
    print(f"\n{name}")
    print("-" * len(name))
    print("PR-AUC: ", average_precision_score(y, p))
    print("ROC-AUC:", roc_auc_score(y, p))
    print("Brier:  ", brier_score_loss(y, p))

evaluate(y_train, y_train_pred, "Train")
evaluate(y_val,   y_val_pred,   "Validation")
evaluate(y_test,  y_test_pred,  "Test")

def top_k_metrics(y_true, y_prob, k_frac):
    """
    y_true: array-like of {0,1}
    y_prob: predicted probabilities
    k_frac: fraction of top predictions to keep (e.g. 0.01 = top 1%)
    """
    n = len(y_true)
    k = int(np.ceil(k_frac * n))

    # Sort by predicted risk descending
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
evaluate_top_k(y_val,  y_val_pred,  "Validation")
evaluate_top_k(y_test, y_test_pred, "Test")


import pandas as pd
import xgboost as xgb

# Paths
SPLIT_DIR = "thesis_data/model_table/splits"
MODEL_PATH = "thesis_data/model/xgb.model"
OUT_PATH = "thesis_data/model/results/xgb_predictions.parquet"

# Load test data
test_df = pd.read_parquet(f"{SPLIT_DIR}/test.parquet")

drop_cols = ["fire_tomorrow", "fire", "date", "year", "cell_id"]
X_test = test_df.drop(columns=drop_cols)
y_test = test_df["fire_tomorrow"]

# Load model
model = xgb.Booster()
model.load_model(MODEL_PATH)

# Predict
dtest = xgb.DMatrix(X_test)
p_test = model.predict(dtest)

# Save minimal prediction table
out_df = test_df[["cell_id", "date", "fire_tomorrow"]].copy()
out_df["p_fire_tomorrow"] = p_test

out_df.to_parquet(OUT_PATH)
print("Saved:", OUT_PATH)

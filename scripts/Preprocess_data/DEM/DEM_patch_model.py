import pandas as pd
import os

MODEL_IN = "thesis_data/model_table/model_table_with_fuel_2015_2024.parquet"
TOPO_V2  = "thesis_data/features/static_topography_by_cell_v2.parquet"
MODEL_OUT = "thesis_data/model_table/model_with_fuel_and_slope_2015_20242.parquet"

df = pd.read_parquet(MODEL_IN)
topo2 = pd.read_parquet(TOPO_V2)[["cell_id", "slope_mean"]]

# drop old slope, merge new slope
df2 = df.drop(columns=["slope_mean"]).merge(topo2, on="cell_id", how="left")

# fill any remaining missing slope with 0 (flat/sea fragments)
df2["slope_mean"] = df2["slope_mean"].fillna(0.0)

os.makedirs("thesis_data/model", exist_ok=True)
df2.to_parquet(MODEL_OUT, index=False)

print("Saved:", MODEL_OUT)
print("Rows:", len(df2))
print("Missing slope:", int(df2["slope_mean"].isna().sum()))
print("Slope range:", df2["slope_mean"].min(), "→", df2["slope_mean"].max())
print(df2[["cell_id", "date", "slope_mean", "fire_tomorrow"]].head())

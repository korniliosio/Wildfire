import pandas as pd
import os
"""Merge static fuel fractions by 10km grid cell from Corine Land Cover data onto model table."""

MODEL_PATH = "thesis_data/model_table/model_table_era5land_2015_2024.parquet"
FUEL_PATH  = "thesis_data/features/static_fuel_fractions_by_cell.parquet"
OUT_PATH   = "thesis_data/model_table/model_table_with_fuel_2015_2024.parquet"

df = pd.read_parquet(MODEL_PATH)
fuel = pd.read_parquet(FUEL_PATH)

# merge fuel onto every row by cell_id
df2 = df.merge(fuel, on="cell_id", how="left")

fuel_cols = [
    "fuel_urban_frac",
    "fuel_agriculture_frac",
    "fuel_grass_frac",
    "fuel_shrub_frac",
    "fuel_forest_frac",
    "fuel_nonburnable_frac",
]

# flag cells where fuel was missing
df2["fuel_missing"] = df2[fuel_cols].isna().any(axis=1).astype("int8")

# fill missing fuel fractions with 0 (safe default; plus we keep the flag)
df2[fuel_cols] = df2[fuel_cols].fillna(0.0)

os.makedirs("thesis_data/model", exist_ok=True)
df2.to_parquet(OUT_PATH, index=False)

print("Saved:", OUT_PATH)
print("Rows:", len(df2))
print("Fuel-missing rows:", int(df2["fuel_missing"].sum()))
print(df2[["cell_id", "fuel_missing"] + fuel_cols].head())

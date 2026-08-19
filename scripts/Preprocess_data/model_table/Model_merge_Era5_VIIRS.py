import pandas as pd
import os
"""Merge daily fire occurrence labels with ERA5-Land weather features by (cell_id, date)."""
labels_path = "thesis_data/model_table/cell_day_labels_2015_2024.parquet"
era5land_path = "thesis_data/features/era5land_cell_day_features_2015_2024.parquet"
out_path = "thesis_data/model_table/model_table_era5land_2015_2024.parquet"

labels = pd.read_parquet(labels_path)
era5land = pd.read_parquet(era5land_path)

# inner join keeps only (cell_id, date) pairs that have ERA5-Land features
model_df = labels.merge(era5land, on=["cell_id", "date"], how="inner")

os.makedirs("thesis_data/model", exist_ok=True)
model_df.to_parquet(out_path, index=False)

print("Saved:", out_path)
print("Rows:", len(model_df))
print("Unique cells:", model_df["cell_id"].nunique())
print("Fire=1 count:", int(model_df["fire"].sum()))
print("Fire rate:", float(model_df["fire"].mean()))
print(model_df.head())

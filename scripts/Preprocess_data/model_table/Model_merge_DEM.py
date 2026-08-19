import pandas as pd
import os

"""Merge static DEM topographic features onto model table with ERA5-Land features."""
MODEL_PATH = "thesis_data/model_table/model_table_with_fuel_2015_2024.parquet"
TOPO_PATH = "thesis_data/features/static_topography_by_cell_v2.parquet"
OUT_PATH = "thesis_data/model_table/model_table_plus_era5land_topo_2015_2024.parquet"

model = pd.read_parquet(MODEL_PATH)
topo = pd.read_parquet(TOPO_PATH)

model2 = model.merge(topo, on="cell_id", how="left")

os.makedirs("thesis_data/model", exist_ok=True)
model2.to_parquet(OUT_PATH, index=False)

print("Saved:", OUT_PATH)
print("Rows:", len(model2))
print("Missing elevation:", int(model2["elev_mean"].isna().sum()))
print("Missing northness:", int(model2["northness_mean"].isna().sum()))
print(model2.head())

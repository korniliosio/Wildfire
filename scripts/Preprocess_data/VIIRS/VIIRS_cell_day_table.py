import geopandas as gpd
import pandas as pd

"""Create full cell-day labels (fire/no fire) for modeling.   """

grid_path = "thesis_data/grid/greece_grid_10km_4326.gpkg"
fire_days_path = "thesis_data/VIIRS/labels/fire_days_by_cell_2015_2024.parquet"
out_path = "thesis_data/model/cell_day_labels_2015_2024.parquet"

# load grid cell ids
grid = gpd.read_file(grid_path)
cell_ids = grid["cell_id"].astype(int).sort_values().unique()

# full daily date range
dates = pd.date_range("2015-01-01", "2024-12-31", freq="D")

# create full index (cartesian product)
base = pd.MultiIndex.from_product(
    [pd.Index(cell_ids), dates],
    names=["cell_id", "date"]
).to_frame(index=False)

# load fire days (positives)
fire_days = pd.read_parquet(fire_days_path)[["cell_id", "date", "fire"]].copy()
fire_days["cell_id"] = fire_days["cell_id"].astype(int)
fire_days["date"] = pd.to_datetime(fire_days["date"])

# merge and fill zeros
labels = base.merge(fire_days, on=["cell_id", "date"], how="left")
labels["fire"] = labels["fire"].fillna(0).astype("int8")

# make output folder
import os
os.makedirs("thesis_data/model", exist_ok=True)

labels.to_parquet(out_path, index=False)

print("Saved:", out_path)
print("Rows (cell-days):", len(labels))
print("Fire=1 count:", int(labels["fire"].sum()))
print("Fire=0 count:", int((labels["fire"] == 0).sum()))
print(labels.head())

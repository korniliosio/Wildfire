import geopandas as gpd
"""Create daily fire occurrence labels by grid cell.   """

in_path = "thesis_data/VIIRS/labels/VIIRS_fires_with_cell_id.gpkg"
out_path = "thesis_data/VIIRS/labels/fire_days_by_cell_2015_2024.parquet"

fires = gpd.read_file(in_path)

# drop fires not assigned to a grid cell
fires = fires.dropna(subset=["cell_id"]).copy()
fires["cell_id"] = fires["cell_id"].astype(int)

# group to daily fire occurrence per cell
fire_days = (
    fires
    .groupby(["cell_id", "date"])
    .size()
    .reset_index(name="n_detections")
)

# binary label
fire_days["fire"] = 1

# save as NEW file (table)
fire_days.to_parquet(out_path, index=False)

print("Saved:", out_path)
print("Fire days:", len(fire_days))
print(fire_days.head())

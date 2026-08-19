import geopandas as gpd
import rasterio
import numpy as np
import pandas as pd
from rasterstats import zonal_stats
import os

"""Extract daily fuel type fractions by 10km grid cell from Corine Land Cover data."""

GRID_PATH = "thesis_data/grid/greece_grid_10km_4326.gpkg"
FUEL_PATH = "thesis_data/corine_landcover/fuel/fuel_types_aligned.tif"
OUT_PATH = "thesis_data/features/static_fuel_fractions_by_cell.parquet"

os.makedirs("thesis_data/features", exist_ok=True)

# fuel code groups
FUEL_GROUPS = {
    "fuel_urban_frac": [1],
    "fuel_agriculture_frac": [2],
    "fuel_grass_frac": [3],
    "fuel_shrub_frac": [4],
    "fuel_forest_frac": [5, 6, 7],
    "fuel_nonburnable_frac": [8],
}

NODATA = 255

# load grid
grid = gpd.read_file(GRID_PATH)[["cell_id", "geometry"]].copy()
grid["cell_id"] = grid["cell_id"].astype(int)

rows = []

print("Computing fuel fractions per cell...")

with rasterio.open(FUEL_PATH) as src:
    fuel_arr = src.read(1)

for idx, row in grid.iterrows():
    geom = row.geometry
    cell_id = row.cell_id

    stats = zonal_stats(
        [geom],
        FUEL_PATH,
        categorical=True,
        nodata=NODATA,
        all_touched=False
    )[0]

    total = sum(stats.values())
    if total == 0:
        total = np.nan

    record = {"cell_id": cell_id}

    for col, codes in FUEL_GROUPS.items():
        count = sum(stats.get(code, 0) for code in codes)
        record[col] = count / total if total > 0 else np.nan

    rows.append(record)

fuel_df = pd.DataFrame(rows)

fuel_df.to_parquet(OUT_PATH, index=False)

print("Saved:", OUT_PATH)
print("Rows:", len(fuel_df))
print("Missing cells:", fuel_df.isna().any(axis=1).sum())
print(fuel_df.head())

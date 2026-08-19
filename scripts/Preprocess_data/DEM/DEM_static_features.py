import geopandas as gpd
import numpy as np
import pandas as pd
from rasterstats import zonal_stats
import os

"""Extract static topographic features by 10km grid cell from DEM data."""

GRID_PATH = "thesis_data/grid/greece_grid_10km_4326.gpkg"
DEM_PATH = "thesis_data/dem/clipped-aligned/dem_data_clipped_aligned.tif"
SLOPE_PATH = "thesis_data/dem/clipped-aligned/slope_aligned_v2.tif"
ASPECT_PATH = "thesis_data/dem/clipped-aligned/aspect_aligned.tif"

OUT_PATH = "thesis_data/features/static_topography_by_cell.parquet"
os.makedirs("thesis_data/features", exist_ok=True)

grid = gpd.read_file(GRID_PATH)[["cell_id", "geometry"]].copy()
grid["cell_id"] = grid["cell_id"].astype(int)

nodata = -9999.0

print("Elevation mean...")
elev = zonal_stats(grid, DEM_PATH, stats=["mean"], nodata=nodata, all_touched=False)
elev_mean = [z["mean"] for z in elev]

print("Slope mean...")
slp = zonal_stats(grid, SLOPE_PATH, stats=["mean"], nodata=nodata, all_touched=False)
slope_mean = [z["mean"] for z in slp]

print("Aspect mean (then to northness/eastness)...")
asp = zonal_stats(grid, ASPECT_PATH, stats=["mean"], nodata=nodata, all_touched=False)
aspect_mean_deg = np.array([z["mean"] for z in asp], dtype="float64")

aspect_rad = np.deg2rad(aspect_mean_deg)
northness_mean = np.cos(aspect_rad)
eastness_mean = np.sin(aspect_rad)

topo = pd.DataFrame({
    "cell_id": grid["cell_id"].values,
    "elev_mean": elev_mean,
    "slope_mean": slope_mean,
    "northness_mean": northness_mean,
    "eastness_mean": eastness_mean,
})

topo.to_parquet(OUT_PATH, index=False)

print("Saved:", OUT_PATH)
print("Rows:", len(topo))
print("Missing elev:", int(topo["elev_mean"].isna().sum()))
print(topo.head())

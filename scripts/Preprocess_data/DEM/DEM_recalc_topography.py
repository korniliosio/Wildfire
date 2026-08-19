import geopandas as gpd
import pandas as pd
from rasterstats import zonal_stats

GRID_PATH = "thesis_data/grid/greece_grid_10km_4326.gpkg"
SLOPE_V2_PATH = "thesis_data/dem/clipped-aligned/slope_aligned_v2.tif"
TOPO_PATH = "thesis_data/features/static_topography_by_cell.parquet"
OUT_TOPO_PATH = "thesis_data/features/static_topography_by_cell_v2.parquet"

grid = gpd.read_file(GRID_PATH)[["cell_id", "geometry"]].copy()
grid["cell_id"] = grid["cell_id"].astype(int)

topo = pd.read_parquet(TOPO_PATH)

print("Computing slope_mean_v2...")
zs = zonal_stats(grid, SLOPE_V2_PATH, stats=["mean"], all_touched=False)
slope_mean_v2 = pd.DataFrame({
    "cell_id": grid["cell_id"].values,
    "slope_mean": [z["mean"] for z in zs]
})

# Patch: replace slope_mean with new values
topo2 = topo.drop(columns=["slope_mean"]).merge(slope_mean_v2, on="cell_id", how="left")

topo2.to_parquet(OUT_TOPO_PATH, index=False)

print("Saved:", OUT_TOPO_PATH)
print("Rows:", len(topo2))
print("Missing slope:", int(topo2["slope_mean"].isna().sum()))
print("Old slope range:", topo["slope_mean"].min(), "→", topo["slope_mean"].max())
print("New slope range:", topo2["slope_mean"].min(), "→", topo2["slope_mean"].max())
print(topo2.head())

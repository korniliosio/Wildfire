import geopandas as gpd
import numpy as np
from shapely.geometry import box
"""
Create a 10 km grid over Greece.
"""

# paths
greece_path = "thesis_data/bounds/greece_4326.shp"
out_grid_path = "thesis_data/grid/greece_grid_10km_4326.gpkg"

# load
greece = gpd.read_file(greece_path)

# project to meters for grid creation
greece_m = greece.to_crs(epsg=3035)

# grid size (10 km)
cell_size = 10_000  # meters

# bounds
minx, miny, maxx, maxy = greece_m.total_bounds

# build grid polygons
xs = np.arange(minx, maxx, cell_size)
ys = np.arange(miny, maxy, cell_size)

cells = []
for x in xs:
    for y in ys:
        cells.append(box(float(x), float(y), float(x + cell_size), float(y + cell_size)))

grid = gpd.GeoDataFrame({"geometry": cells}, crs=greece_m.crs)

# clip grid to Greece
grid = gpd.overlay(grid, greece_m[["geometry"]], how="intersection")

# add id
grid = grid.reset_index(drop=True)
grid["cell_id"] = grid.index.astype(int)

# save in EPSG:4326 (lat/lon)
grid_4326 = grid.to_crs(epsg=4326)

# make sure output folder exists (safe)
import os
os.makedirs("thesis_data/grid", exist_ok=True)

grid_4326.to_file(out_grid_path, driver="GPKG")

print("Saved:", out_grid_path)
print("Grid cells:", len(grid_4326))
print("CRS:", grid_4326.crs)
print(grid_4326.head())

# make_fig1_grid_map.py
import os
import geopandas as gpd
import matplotlib.pyplot as plt

# ---- EDIT THESE ----
GRID_PATH = "thesis_data/grid/greece_grid_10km_4326.gpkg"   # e.g., .gpkg, .shp, .geojson
GRID_LAYER = None                         # e.g., "grid" if needed; else None
OUT_PNG = "thesis/figures/fig1_grid_map.png"
# --------------------

def read_grid(path, layer=None):
    if layer is None:
        return gpd.read_file(path)
    return gpd.read_file(path, layer=layer)

grid = read_grid(GRID_PATH, GRID_LAYER)

# If it's points (centroids), this will still plot, but grid polygons are preferred
if grid.crs is None:
    raise ValueError("Grid CRS is missing. Set CRS before plotting.")

# Plot
fig, ax = plt.subplots(figsize=(8, 9))
grid.boundary.plot(ax=ax, linewidth=0.3)

# Optional: bounding box / extent cleanup
minx, miny, maxx, maxy = grid.total_bounds
pad_x = (maxx - minx) * 0.05
pad_y = (maxy - miny) * 0.05
ax.set_xlim(minx - pad_x, maxx + pad_x)
ax.set_ylim(miny - pad_y, maxy + pad_y)

ax.set_title("Study Area and Modeling Grid (Greece)", fontsize=14)
ax.set_xlabel("Longitude" if grid.crs.is_geographic else "Easting")
ax.set_ylabel("Latitude" if grid.crs.is_geographic else "Northing")
ax.set_aspect("equal", adjustable="box")

plt.tight_layout()
# ensure output directory exists
out_dir = os.path.dirname(OUT_PNG)
if out_dir:
    os.makedirs(out_dir, exist_ok=True)
plt.savefig(OUT_PNG, dpi=300)
print("Saved:", OUT_PNG)

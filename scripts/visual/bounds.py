import os
import geopandas as gpd
import matplotlib.pyplot as plt

# Paths
GREECE_PATH = "thesis_data/bounds/greece_4326.shp"
GRID_PATH = "thesis_data/grid/greece_grid_10km_4326.gpkg"

OUT_DIR = "thesis/figures"
os.makedirs(OUT_DIR, exist_ok=True)

greece = gpd.read_file(GREECE_PATH)
grid = gpd.read_file(GRID_PATH)

# Ensure same CRS
greece = greece.to_crs("EPSG:4326")
grid = grid.to_crs("EPSG:4326")

# -----------------------------
# Figure 1: Study Area
# -----------------------------
fig, ax = plt.subplots(figsize=(7, 8))

greece.plot(
    ax=ax,
    facecolor="#f8fafc",
    edgecolor="#111827",
    linewidth=0.8
)

minx, miny, maxx, maxy = greece.total_bounds
pad_x = (maxx - minx) * 0.08
pad_y = (maxy - miny) * 0.08

ax.set_xlim(minx - pad_x, maxx + pad_x)
ax.set_ylim(miny - pad_y, maxy + pad_y)

ax.set_title("Study Area: Greece", fontsize=14, fontweight="bold")
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
ax.set_aspect("equal", adjustable="box")
ax.grid(True, linewidth=0.3, alpha=0.4)

plt.tight_layout()
plt.savefig(f"{OUT_DIR}/study_area_greece.png", dpi=300)
plt.close()

# -----------------------------
# Figure 2: Study Area + Grid
# -----------------------------
fig, ax = plt.subplots(figsize=(7, 8))

greece.plot(
    ax=ax,
    facecolor="#f8fafc",
    edgecolor="#111827",
    linewidth=0.8
)

grid.boundary.plot(
    ax=ax,
    color="#ef4444",
    linewidth=0.25,
    alpha=0.75
)

ax.set_xlim(minx - pad_x, maxx + pad_x)
ax.set_ylim(miny - pad_y, maxy + pad_y)

ax.set_title("Greece Study Area and 10 km Analysis Grid", fontsize=14, fontweight="bold")
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
ax.set_aspect("equal", adjustable="box")
ax.grid(True, linewidth=0.3, alpha=0.4)

plt.tight_layout()
plt.savefig(f"{OUT_DIR}/study_area_grid.png", dpi=300)
plt.close()

print("Saved:")
print(f"{OUT_DIR}/study_area_greece.png")
print(f"{OUT_DIR}/study_area_grid.png")
import os
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

# =========================
# CONFIG
# =========================

DATE = "2023-08-22"  # change this to any date with fires

GRID_PATH = "thesis_data/grid/greece_grid_10km_4326.gpkg"
VIIRS_PATH = "thesis_data/VIIRS/labels/VIIRS_fires_with_cell_id.gpkg"
LABELS_PATH = "thesis_data/VIIRS/labels/fire_days_by_cell_2015_2024.parquet"
OUT_DIR = "thesis/figures"
os.makedirs(OUT_DIR, exist_ok=True)

OUT_MAP = f"{OUT_DIR}/fire_label_generation_{DATE}.png"
OUT_TABLE = f"{OUT_DIR}/fire_class_distribution.csv"


# =========================
# LOAD DATA
# =========================

grid = gpd.read_file(GRID_PATH).to_crs("EPSG:4326")
viirs = gpd.read_file(VIIRS_PATH).to_crs("EPSG:4326")
labels = pd.read_parquet(LABELS_PATH)

labels["date"] = pd.to_datetime(labels["date"])
date_obj = pd.to_datetime(DATE)

# Filter selected date
labels_day = labels[labels["date"] == date_obj].copy()
viirs_day = viirs[pd.to_datetime(viirs["ACQ_DATE"]) == date_obj].copy()

# Merge labels onto grid
grid_day = grid.merge(
    labels_day[["cell_id", "fire"]],
    on="cell_id",
    how="left"
)

grid_day["fire"] = grid_day["fire"].fillna(0).astype(int)

fire_cells = grid_day[grid_day["fire"] == 1]
no_fire_cells = grid_day[grid_day["fire"] == 0]


# =========================
# CREATE MAP FIGURE
# =========================

fig, axes = plt.subplots(1, 2, figsize=(14, 8))

# Common map extent
minx, miny, maxx, maxy = grid.total_bounds
pad_x = (maxx - minx) * 0.05
pad_y = (maxy - miny) * 0.05

# ---- Left: VIIRS detections ----
ax = axes[0]

grid.boundary.plot(
    ax=ax,
    color="#94a3b8",
    linewidth=0.25,
    alpha=0.6
)

if not viirs_day.empty:
    viirs_day.plot(
        ax=ax,
        color="#dc2626",
        markersize=18,
        alpha=0.9
    )

ax.set_title(f"VIIRS Active Fire Detections\n{DATE}", fontsize=13, fontweight="bold")
ax.set_xlim(minx - pad_x, maxx + pad_x)
ax.set_ylim(miny - pad_y, maxy + pad_y)
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
ax.set_aspect("equal", adjustable="box")
ax.grid(True, linewidth=0.3, alpha=0.35)


# ---- Right: generated fire labels ----
ax = axes[1]

no_fire_cells.plot(
    ax=ax,
    facecolor="#f1f5f9",
    edgecolor="#cbd5e1",
    linewidth=0.2
)

fire_cells.plot(
    ax=ax,
    facecolor="#dc2626",
    edgecolor="#7f1d1d",
    linewidth=0.5
)

ax.set_title(f"Generated Grid Fire Labels\nfire = 1 if cell contains VIIRS detection", fontsize=13, fontweight="bold")
ax.set_xlim(minx - pad_x, maxx + pad_x)
ax.set_ylim(miny - pad_y, maxy + pad_y)
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
ax.set_aspect("equal", adjustable="box")
ax.grid(True, linewidth=0.3, alpha=0.35)


plt.tight_layout()
plt.savefig(OUT_MAP, dpi=300, bbox_inches="tight")
plt.close()

print(f"Saved map: {OUT_MAP}")


# =========================
# CLASS DISTRIBUTION TABLE
# =========================

class_counts = labels["fire"].value_counts().sort_index()
class_distribution = pd.DataFrame({
    "class": ["No fire", "Fire"],
    "label_value": [0, 1],
    "count": [
        int(class_counts.get(0, 0)),
        int(class_counts.get(1, 0))
    ]
})

class_distribution["percentage"] = (
    class_distribution["count"] / class_distribution["count"].sum() * 100
).round(4)

class_distribution.to_csv(OUT_TABLE, index=False)

print(f"Saved class distribution table: {OUT_TABLE}")
print(class_distribution)
# make_feature_map_grid.py
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np

# -------------------- EDIT THESE --------------------
PARQUET_PATH = "thesis_data/model_table/model_table_nextday_2015_2024_final.parquet"
GRID_PATH    = "thesis_data/grid/greece_grid_10km_4326.gpkg"   # must contain cell_id + geometry
GRID_LAYER   = None                           # e.g. "grid" or None
DATE_STR     = "2023-08-21"                   # pick a date to visualize
OUT_PNG      = "thesis/figures/fig_feature_maps_" + DATE_STR + ".png"
# ----------------------------------------------------

# Which variables to plot (edit freely)
PLOT_COLS = [
    "temp_daily_max_C",
    "rh_daily_min",
    "wind_daily_max",
    "elev_mean",
    "slope_mean",
    "fuel_forest_frac",
    "fuel_shrub_frac",
    "fuel_agriculture_frac",
    "fuel_nonburnable_frac",
    "fire",            # today's fire mask (if you kept it)
    "fire_tomorrow",   # tomorrow label mask
]

def read_grid(path, layer=None):
    g = gpd.read_file(path) if layer is None else gpd.read_file(path, layer=layer)
    if "cell_id" not in g.columns:
        raise ValueError("Grid file must contain a 'cell_id' column.")
    if g.crs is None:
        raise ValueError("Grid CRS is missing. Please set CRS on the grid.")
    return g[["cell_id", "geometry"]].copy()

# Load
df = pd.read_parquet(PARQUET_PATH)
df["date"] = pd.to_datetime(df["date"])
date = pd.to_datetime(DATE_STR)

# Filter one day
day = df.loc[df["date"] == date, ["cell_id", "date"] + [c for c in PLOT_COLS if c in df.columns]].copy()
if day.empty:
    raise ValueError(f"No rows found for date {DATE_STR}. Check the date format and coverage.")

# Load grid and merge geometry
grid = read_grid(GRID_PATH, GRID_LAYER)
gdf = grid.merge(day, on="cell_id", how="inner")
gdf = gpd.GeoDataFrame(gdf, geometry="geometry", crs=grid.crs)

# Plot layout
n = len(PLOT_COLS)
ncols = 6                           # change to 5/6/7 depending on how wide you want it
nrows = int(np.ceil(n / ncols))

fig_w = 3.0 * ncols
fig_h = 3.0 * nrows
fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=(fig_w, fig_h))
axes = np.array(axes).reshape(-1)

# Plot each panel
for i, col in enumerate(PLOT_COLS):
    ax = axes[i]
    ax.set_axis_off()

    if col not in gdf.columns:
        ax.set_title(f"{col}\n(missing)", fontsize=10)
        continue

    # Categorical-ish masks get clean plotting
    if col in ["fire", "fire_tomorrow"]:
        gdf.plot(column=col, ax=ax, legend=False)  # default colormap is fine
        ax.set_title(col, fontsize=10)
    else:
        # Robust scaling (avoids one outlier washing out the map)
        s = gdf[col]
        vmin = s.quantile(0.02)
        vmax = s.quantile(0.98)
        gdf.plot(column=col, ax=ax, vmin=vmin, vmax=vmax, legend=True,
                 legend_kwds={"shrink": 0.6})
        ax.set_title(col, fontsize=10)

# Turn off unused axes
for j in range(n, len(axes)):
    axes[j].set_visible(False)

fig.suptitle(f"Spatial Feature Maps — {DATE_STR}", fontsize=16)
plt.tight_layout()
plt.savefig(OUT_PNG, dpi=300)
print("Saved:", OUT_PNG)

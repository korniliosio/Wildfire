import os
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

# ----------------------------
# Paths (EDIT THESE)
# ----------------------------
GRID_GPKG = "thesis_data/grid/greece_grid_10km_4326.gpkg"
GRID_LAYER = None  # set to layer name string if gpkg has multiple layers, else keep None

GREECE_SHP = "thesis_data/bounds/greece_4326.shp"

PRED_PATH = "thesis_data/model/results/xgb_predictions.parquet"

OUT_DIR = "thesis/figures/maps"
os.makedirs(OUT_DIR, exist_ok=True)

# ----------------------------
# Helpers
# ----------------------------
def load_grid():
    if GRID_LAYER is None:
        gdf = gpd.read_file(GRID_GPKG)
    else:
        gdf = gpd.read_file(GRID_GPKG, layer=GRID_LAYER)
    if "cell_id" not in gdf.columns:
        raise ValueError(f"'cell_id' not found in grid columns: {list(gdf.columns)[:30]}")
    return gdf

def load_greece():
    greece = gpd.read_file(GREECE_SHP)
    # dissolve to single geometry for clean outline
    greece = greece.dissolve()
    return greece

def ensure_same_crs(grid, greece):
    if grid.crs is None:
        raise ValueError("Grid CRS is None. Please ensure grid has a CRS.")
    if greece.crs is None:
        raise ValueError("Greece boundary CRS is None. Please ensure boundary has a CRS.")
    if grid.crs != greece.crs:
        greece = greece.to_crs(grid.crs)
    return grid, greece

def clip_to_greece(grid, greece):
    # Clip for nicer maps; if clip is slow, you can skip and just plot boundary outline
    try:
        return gpd.clip(grid, greece)
    except Exception:
        # fallback: spatial join mask
        mask = grid.geometry.centroid.within(greece.geometry.iloc[0])
        return grid.loc[mask].copy()

def pick_dates(pred_df):
    """
    Pick 3 dates:
      - 'max_fires': date with the most fires_tomorrow == 1
      - 'high_risk': date with high total predicted risk but not necessarily max fires
      - 'quiet': date with low total predicted risk and few fires
    """
    pred_df["date"] = pd.to_datetime(pred_df["date"])

    daily = pred_df.groupby("date").agg(
        fires=("fire_tomorrow", "sum"),
        mean_risk=("p_fire_tomorrow", "mean"),
        total_risk=("p_fire_tomorrow", "sum"),
        n=("p_fire_tomorrow", "size")
    ).reset_index()

    max_fires_date = daily.sort_values(["fires", "total_risk"], ascending=False).iloc[0]["date"]

    # choose high-risk day among top 10% total_risk, but not the same as max_fires_date if possible
    top = daily[daily["total_risk"] >= daily["total_risk"].quantile(0.90)].copy()
    top = top[top["date"] != max_fires_date]
    if len(top) == 0:
        high_risk_date = daily.sort_values("total_risk", ascending=False).iloc[1]["date"]
    else:
        high_risk_date = top.sort_values("total_risk", ascending=False).iloc[0]["date"]

    # quiet day: among bottom 10% total_risk, pick minimal fires then minimal total_risk
    bot = daily[daily["total_risk"] <= daily["total_risk"].quantile(0.10)].copy()
    quiet_date = bot.sort_values(["fires", "total_risk"], ascending=True).iloc[0]["date"]

    return {
        "max_fires": pd.Timestamp(max_fires_date),
        "high_risk": pd.Timestamp(high_risk_date),
        "quiet": pd.Timestamp(quiet_date),
        "daily_table": daily
    }

def plot_daily_map(gdf_day, greece_outline, title, out_path, vmax=None):
    fig, ax = plt.subplots(figsize=(8, 10))
    ax.set_axis_off()

    # choose robust vmax
    if vmax is None:
        vmax = float(gdf_day["p_fire_tomorrow"].quantile(0.99))

    gdf_day.plot(
        column="p_fire_tomorrow",
        ax=ax,
        legend=True,
        vmin=0.0,
        vmax=vmax
    )

    # Outline
    greece_outline.boundary.plot(ax=ax, linewidth=1)

    # Fires overlay: mark cells where fire_tomorrow==1
    fires = gdf_day[gdf_day["fire_tomorrow"] == 1]
    if len(fires) > 0:
        fires.centroid.plot(ax=ax, markersize=12)

    ax.set_title(title)
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close(fig)

def plot_topk_map(gdf_day, greece_outline, k=0.01, title="", out_path="topk.png"):
    fig, ax = plt.subplots(figsize=(8, 10))
    ax.set_axis_off()

    thr = float(gdf_day["p_fire_tomorrow"].quantile(1 - k))
    gdf_day["topk"] = (gdf_day["p_fire_tomorrow"] >= thr).astype(int)

    gdf_day.plot(
        column="topk",
        ax=ax,
        legend=False
    )
    greece_outline.boundary.plot(ax=ax, linewidth=1)

    fires = gdf_day[gdf_day["fire_tomorrow"] == 1]
    if len(fires) > 0:
        fires.centroid.plot(ax=ax, markersize=12)

    ax.set_title(title + f" (Top {k*100:.1f}%)")
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close(fig)

def plot_mean_risk_hotspots(grid_geom, pred_df, greece_outline, out_path):
    # mean risk across all test dates
    mean_risk = pred_df.groupby("cell_id")["p_fire_tomorrow"].mean().reset_index()
    gdf = grid_geom.merge(mean_risk, on="cell_id", how="left")

    fig, ax = plt.subplots(figsize=(8, 10))
    ax.set_axis_off()

    vmax = float(gdf["p_fire_tomorrow"].quantile(0.99))
    gdf.plot(column="p_fire_tomorrow", ax=ax, legend=True, vmin=0.0, vmax=vmax)
    greece_outline.boundary.plot(ax=ax, linewidth=1)
    ax.set_title("Mean predicted next-day fire risk (Test period)")
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close(fig)

# ----------------------------
# Main
# ----------------------------
grid = load_grid()
greece = load_greece()
grid, greece = ensure_same_crs(grid, greece)

grid_clip = clip_to_greece(grid, greece)

pred = pd.read_parquet(PRED_PATH)
needed = {"cell_id", "date", "fire_tomorrow", "p_fire_tomorrow"}
missing = needed - set(pred.columns)
if missing:
    raise ValueError(f"Predictions file missing columns: {missing}")

picked = pick_dates(pred)
dates = picked["max_fires"], picked["high_risk"], picked["quiet"]

# Use a consistent color scale across daily plots (99th percentile over all rows)
global_vmax = float(pred["p_fire_tomorrow"].quantile(0.99))

for label, day in [("max_fires", dates[0]), ("high_risk", dates[1]), ("quiet", dates[2])]:
    pred_day = pred[pred["date"] == day].copy()
    gdf_day = grid_clip.merge(pred_day, on="cell_id", how="inner")

    fire_count = int(gdf_day["fire_tomorrow"].sum())
    title = f"{label.replace('_',' ').title()} — {day.date()} | fires tomorrow: {fire_count}"

    out_path = os.path.join(OUT_DIR, f"daily_{label}_{day.date()}.png")
    plot_daily_map(gdf_day, greece, title, out_path, vmax=global_vmax)
    print("Saved:", out_path)

# Top-1% map for the max-fires day (most persuasive)
day = dates[0]
pred_day = pred[pred["date"] == day].copy()
gdf_day = grid_clip.merge(pred_day, on="cell_id", how="inner")
out_path = os.path.join(OUT_DIR, f"top1pct_{day.date()}.png")
plot_topk_map(gdf_day, greece, k=0.01, title=f"XGBoost predicted risk — {day.date()}", out_path=out_path)
print("Saved:", out_path)

# Mean hotspot map across test period
out_path = os.path.join(OUT_DIR, "mean_risk_test_period.png")
plot_mean_risk_hotspots(grid_clip, pred, greece, out_path)
print("Saved:", out_path)

print("\nPicked dates:")
print("max_fires:", picked["max_fires"].date())
print("high_risk:", picked["high_risk"].date())
print("quiet:", picked["quiet"].date())

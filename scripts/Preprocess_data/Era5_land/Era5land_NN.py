import os
import glob
import numpy as np
import pandas as pd
import xarray as xr
import geopandas as gpd

RAW_DIR   = "thesis_data/era5land_hourly/raw"
GRID_PATH = "thesis_data/grid/greece_grid_10km_4326.gpkg"
OUT_PATH  = "thesis_data/features/era5land_cell_day_features_2015_2024.parquet"

TIME_DIM = "valid_time"

os.makedirs("thesis_data/features", exist_ok=True)

def rh_from_t_td(t_k, td_k):
    """Relative humidity (%) from temperature and dewpoint (Kelvin)."""
    t_c = t_k - 273.15
    td_c = td_k - 273.15
    es_td = np.exp((17.625 * td_c) / (243.04 + td_c))
    es_t  = np.exp((17.625 * t_c)  / (243.04 + t_c))
    rh = 100.0 * (es_td / es_t)
    return np.clip(rh, 0, 100).astype(np.float32)

def daily_agg(ds):
    # Remove singleton dims if present
    for dim in ["number", "expver"]:
        if dim in ds.dims:
            ds = ds.isel({dim: 0})

    t2m = ds["t2m"].astype("float32")
    d2m = ds["d2m"].astype("float32")
    u10 = ds["u10"].astype("float32")
    v10 = ds["v10"].astype("float32")

    wind = np.sqrt(u10**2 + v10**2)

    temp_daily_max_C = (t2m - 273.15).resample({TIME_DIM: "1D"}).max()

    rh_hourly = xr.apply_ufunc(
        rh_from_t_td, t2m, d2m,
        dask="allowed",
        output_dtypes=[np.float32]
    )
    rh_daily_min = rh_hourly.resample({TIME_DIM: "1D"}).min()

    wind_daily_max = wind.resample({TIME_DIM: "1D"}).max()

    return temp_daily_max_C, rh_daily_min, wind_daily_max

def compute_centroids_latlon(grid_gdf):
    """Compute centroids in meters (3857) then return lat/lon in EPSG:4326."""
    g = grid_gdf.copy()
    if g.crs is None:
        g = g.set_crs("EPSG:4326")
    g4326 = g.to_crs("EPSG:4326")
    g3857 = g4326.to_crs("EPSG:3857")
    cent_3857 = g3857.geometry.centroid
    cent_4326 = gpd.GeoSeries(cent_3857, crs="EPSG:3857").to_crs("EPSG:4326")
    return cent_4326.y.values.astype(np.float64), cent_4326.x.values.astype(np.float64)

def build_nearest_valid_index(ds_sample, cell_lats, cell_lons):
    """
    For each cell centroid, find the nearest ERA5 gridpoint that is VALID (non-NaN)
    according to t2m at time 0 in the sample dataset.
    Returns arrays (era_i, era_j) with length n_cells.
    """
    # Drop singleton dims
    t2m = ds_sample["t2m"]
    for dim in ["number", "expver"]:
        if dim in t2m.dims:
            t2m = t2m.isel({dim: 0})

    lat_grid = ds_sample["latitude"].values
    lon_grid = ds_sample["longitude"].values

    # Valid mask at time 0
    t2m0 = t2m.isel({TIME_DIM: 0}).values  # (lat, lon)
    valid = np.isfinite(t2m0)

    valid_i, valid_j = np.where(valid)
    valid_lats = lat_grid[valid_i]
    valid_lons = lon_grid[valid_j]

    print("ERA5 grid points:", valid.size)
    print("Valid ERA5 points:", len(valid_i), f"({valid.mean()*100:.2f}% valid)")

    era_i = np.empty(len(cell_lats), dtype=np.int32)
    era_j = np.empty(len(cell_lats), dtype=np.int32)

    # Brute-force nearest valid point (2059 cells x ~3-4k valid points => fine)
    for c in range(len(cell_lats)):
        d2 = (valid_lats - cell_lats[c])**2 + (valid_lons - cell_lons[c])**2
        k = int(np.argmin(d2))
        era_i[c] = int(valid_i[k])
        era_j[c] = int(valid_j[k])

    return era_i, era_j

# ------------------------
# Load grid + centroids
# ------------------------
grid = gpd.read_file(GRID_PATH)[["cell_id", "geometry"]].copy()
grid["cell_id"] = grid["cell_id"].astype(int)
grid = grid.to_crs("EPSG:4326")

cell_lats, cell_lons = compute_centroids_latlon(grid)

coords = pd.DataFrame({
    "cell_id": grid["cell_id"].values,
    "lat": cell_lats,
    "lon": cell_lons
}).sort_values("cell_id").reset_index(drop=True)

# ------------------------
# Build nearest-valid lookup using a sample file
# ------------------------
files = sorted(glob.glob(os.path.join(RAW_DIR, "era5land_greece_*.nc")))
if not files:
    raise FileNotFoundError(f"No NetCDF files found in {RAW_DIR}")

print("Monthly files:", len(files))
print("Using sample for mask:", os.path.basename(files[0]))

ds0 = xr.open_dataset(files[0])
era_i, era_j = build_nearest_valid_index(ds0, coords["lat"].values, coords["lon"].values)

coords["era_i"] = era_i
coords["era_j"] = era_j

print("Unique ERA5 points used:", len(set(zip(era_i.tolist(), era_j.tolist()))))

# ------------------------
# Process all files
# ------------------------
all_parts = []

for fp in files:
    print("Processing:", os.path.basename(fp))
    ds = xr.open_dataset(fp)

    tmaxC, rhmin, wmax = daily_agg(ds)

    # Sample by integer indices -> always valid points
    tmaxC_s = tmaxC.isel(
        latitude=xr.DataArray(coords["era_i"].values, dims="cell"),
        longitude=xr.DataArray(coords["era_j"].values, dims="cell"),
    )
    rhmin_s = rhmin.isel(
        latitude=xr.DataArray(coords["era_i"].values, dims="cell"),
        longitude=xr.DataArray(coords["era_j"].values, dims="cell"),
    )
    wmax_s = wmax.isel(
        latitude=xr.DataArray(coords["era_i"].values, dims="cell"),
        longitude=xr.DataArray(coords["era_j"].values, dims="cell"),
    )

    dates = pd.to_datetime(tmaxC_s[TIME_DIM].values)

    part = pd.DataFrame({
        "date": np.repeat(dates, len(coords)),
        "cell_id": np.tile(coords["cell_id"].values, len(dates)),
        "temp_daily_max_C": tmaxC_s.values.reshape(-1).astype(np.float32),
        "rh_daily_min": rhmin_s.values.reshape(-1).astype(np.float32),
        "wind_daily_max": wmax_s.values.reshape(-1).astype(np.float32),
    })

    all_parts.append(part)

df_all = pd.concat(all_parts, ignore_index=True)
df_all["date"] = pd.to_datetime(df_all["date"])
df_all = df_all.sort_values(["cell_id", "date"]).reset_index(drop=True)

# Final sanity checks
nan_rows = df_all[["temp_daily_max_C", "rh_daily_min", "wind_daily_max"]].isna().any(axis=1).sum()
print("Rows:", len(df_all))
print("Unique cells:", df_all["cell_id"].nunique())
print("Date range:", df_all["date"].min(), "→", df_all["date"].max())
print("Rows with any NaN weather:", int(nan_rows))

df_all.to_parquet(OUT_PATH, index=False)
print("Saved:", OUT_PATH)
print(df_all.head(10))

import os
import glob
import numpy as np
import pandas as pd
import xarray as xr
import rasterio
"""Extract daily ERA5-Land weather features by 10km grid cell for 2015-2024.
    The features are:
    - daily max 2m air temperature (°C)
    - daily min 2m relative humidity (%)
    - daily max 10m wind speed (m/s)
"""

RAW_DIR = "thesis_data/era5land_hourly/raw"
ZONE_PATH = "thesis_data/features/grid_cell_id_zones_era5land.tif"
OUT_PATH = "thesis_data/features/era5land_cell_day_features_2015_2024.parquet"

os.makedirs("thesis_data/features", exist_ok=True)

# --- Load zones once ---
with rasterio.open(ZONE_PATH) as zsrc:
    zones = zsrc.read(1)
valid_mask = zones != -1
zone_ids = zones[valid_mask].astype(int)

TIME_DIM = "valid_time"

def rh_from_t_td(t_k, td_k):
    """Relative humidity (%) from temperature and dewpoint (Kelvin)."""
    t_c = t_k - 273.15
    td_c = td_k - 273.15
    es_td = np.exp((17.625 * td_c) / (243.04 + td_c))
    es_t  = np.exp((17.625 * t_c)  / (243.04 + t_c))
    rh = 100.0 * (es_td / es_t)
    return np.clip(rh, 0, 100)

def daily_agg(ds):
    # Remove singleton dims if present (sometimes CDS adds them)
    for dim in ["number", "expver"]:
        if dim in ds.dims:
            ds = ds.isel({dim: 0})

    t2m = ds["t2m"].astype("float32")
    d2m = ds["d2m"].astype("float32")
    u10 = ds["u10"].astype("float32")
    v10 = ds["v10"].astype("float32")

    wind = np.sqrt(u10**2 + v10**2)

    # Daily aggregations along valid_time
    temp_daily_max_C = (t2m - 273.15).resample({TIME_DIM: "1D"}).max()

    rh_hourly = xr.apply_ufunc(
        rh_from_t_td, t2m, d2m,
        dask="allowed",
        output_dtypes=[np.float32]
    )
    rh_daily_min = rh_hourly.resample({TIME_DIM: "1D"}).min()

    wind_daily_max = wind.resample({TIME_DIM: "1D"}).max()

    return temp_daily_max_C, rh_daily_min, wind_daily_max

def cell_means_from_daily(daily_da, dates, colname):
    out_rows = []
    # iterate over time index
    for i in range(daily_da.sizes[TIME_DIM]):
        arr = daily_da.isel({TIME_DIM: i}).values
        vals = arr[valid_mask]
        df = (
            pd.DataFrame({"cell_id": zone_ids, colname: vals})
            .groupby("cell_id", as_index=False)[colname].mean()
        )
        df["date"] = pd.to_datetime(dates[i]).date()
        out_rows.append(df)
    return pd.concat(out_rows, ignore_index=True)

files = sorted(glob.glob(os.path.join(RAW_DIR, "era5land_greece_*.nc")))
print("Monthly files:", len(files))

all_parts = []

for fp in files:
    print("Processing:", os.path.basename(fp))
    ds = xr.open_dataset(fp)

    tmaxC, rhmin, wmax = daily_agg(ds)

    # daily dates from the resampled object
    dates = pd.to_datetime(tmaxC[TIME_DIM].values)

    part_t = cell_means_from_daily(tmaxC, dates, "temp_daily_max_C")
    part_r = cell_means_from_daily(rhmin, dates, "rh_daily_min")
    part_w = cell_means_from_daily(wmax, dates, "wind_daily_max")

    part = part_t.merge(part_r, on=["cell_id", "date"], how="inner")
    part = part.merge(part_w, on=["cell_id", "date"], how="inner")

    all_parts.append(part)

df_all = pd.concat(all_parts, ignore_index=True)
df_all["date"] = pd.to_datetime(df_all["date"])
df_all = df_all.sort_values(["cell_id", "date"])

df_all.to_parquet(OUT_PATH, index=False)

print("Saved:", OUT_PATH)
print("Rows:", len(df_all))
print("Years covered:", df_all["date"].dt.year.min(), "→", df_all["date"].dt.year.max())
print("Unique cells:", df_all["cell_id"].nunique())
print(df_all.head())

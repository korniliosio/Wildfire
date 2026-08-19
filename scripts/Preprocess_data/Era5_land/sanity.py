#!/usr/bin/env python3
"""
diagnose_era5land_sampling.py

A comprehensive diagnostic script to identify WHY ERA5-Land values become NaN
when extracting weather features for your grid.

It tests:
1) NetCDF integrity: dims/coords, variable presence, dtype, missing-value attributes
2) Spatial mask: fraction of NaNs by variable at a timestep + consistency across time
3) Temporal coverage: missing fraction over time (hourly) and after daily aggregation
4) Grid ↔ ERA5 alignment: centroid nearest-point mapping, how many map to NaN points
5) Zone rasterization health (optional): if you provide a zone tif, it checks zero-pixel cells
6) Outputs: CSVs of problematic cells and optional quick plots (png)

Run:
  python scripts/Preprocess_data/Era5_land/sanity.py \
    --grid thesis_data/grid/greece_grid_10km_4326.gpkg \
    --nc thesis_data/era5land_hourly/raw/era5land_greece_2015_01.nc \
    --outdir thesis_data/diagnostics/era5land

Optional:
  --zone thesis_data/features/grid_cell_id_zones_era5land.tif
"""

import os
import json
import argparse
import numpy as np
import pandas as pd
import xarray as xr
import geopandas as gpd

# Optional plotting deps
try:
    import matplotlib.pyplot as plt
    HAS_PLT = True
except Exception:
    HAS_PLT = False

try:
    import rasterio
    HAS_RIO = True
except Exception:
    HAS_RIO = False


TIME_DIM_DEFAULT = "valid_time"
LAT_NAMES = ["latitude", "lat"]
LON_NAMES = ["longitude", "lon"]
VARS_EXPECTED = ["t2m", "d2m", "u10", "v10"]


def find_coord_name(ds, candidates):
    for c in candidates:
        if c in ds.coords or c in ds.variables:
            return c
    return None


def safe_item(x):
    try:
        return x.item()
    except Exception:
        return x


def describe_da(da: xr.DataArray, time_dim: str, lat_name: str, lon_name: str):
    """Return a dict of diagnostics for a DataArray."""
    info = {}
    info["name"] = da.name
    info["dtype"] = str(da.dtype)
    info["dims"] = list(da.dims)
    info["shape"] = list(da.shape)
    info["attrs"] = {k: safe_item(v) for k, v in da.attrs.items() if k in ["units", "long_name", "standard_name", "_FillValue", "missing_value"]}

    # overall missing fraction
    vals = da.values
    info["nan_frac_overall"] = float(np.isnan(vals).mean())

    # per-time missing fraction (sample up to 10 times)
    if time_dim in da.dims:
        T = da.sizes[time_dim]
        idxs = np.unique(np.linspace(0, T - 1, num=min(10, T), dtype=int))
        per_t = []
        for i in idxs:
            sl = da.isel({time_dim: i}).values
            per_t.append(float(np.isnan(sl).mean()))
        info["nan_frac_time_samples"] = {"indices": idxs.tolist(), "nan_fracs": per_t}

    # spatial-only missing fraction at first timestep if time exists
    if time_dim in da.dims:
        sl0 = da.isel({time_dim: 0}).values
        info["nan_frac_t0"] = float(np.isnan(sl0).mean())

    # min/max on finite values
    finite = np.isfinite(vals)
    if finite.any():
        info["min_finite"] = float(vals[finite].min())
        info["max_finite"] = float(vals[finite].max())
        info["p01"] = float(np.quantile(vals[finite], 0.01))
        info["p99"] = float(np.quantile(vals[finite], 0.99))
    else:
        info["min_finite"] = None
        info["max_finite"] = None
        info["p01"] = None
        info["p99"] = None

    return info


def rh_from_t_td_np(t_k, td_k):
    """Relative humidity (%) from temperature and dewpoint (Kelvin)."""
    t_c = t_k - 273.15
    td_c = td_k - 273.15
    es_td = np.exp((17.625 * td_c) / (243.04 + td_c))
    es_t  = np.exp((17.625 * t_c)  / (243.04 + t_c))
    rh = 100.0 * (es_td / es_t)
    return np.clip(rh, 0, 100)


def daily_agg_simple(ds, time_dim, lat_name, lon_name):
    """Compute daily tmax (C), rhmin (%), wmax (m/s) with minimal assumptions."""
    # drop singleton dims if present
    for dim in ["number", "expver"]:
        if dim in ds.dims:
            ds = ds.isel({dim: 0})

    t2m = ds["t2m"].astype("float32")
    d2m = ds["d2m"].astype("float32")
    u10 = ds["u10"].astype("float32")
    v10 = ds["v10"].astype("float32")
    wind = np.sqrt(u10**2 + v10**2)

    tmaxC = (t2m - 273.15).resample({time_dim: "1D"}).max()

    # RH hourly from numpy on values through apply_ufunc
    rh_hourly = xr.apply_ufunc(
        rh_from_t_td_np, t2m, d2m,
        dask="allowed",
        output_dtypes=[np.float32]
    )
    rhmin = rh_hourly.resample({time_dim: "1D"}).min()

    wmax = wind.resample({time_dim: "1D"}).max()

    return tmaxC, rhmin, wmax


def compute_centroids_latlon(grid_gdf: gpd.GeoDataFrame):
    """Compute centroids robustly in projected CRS then convert to EPSG:4326."""
    g = grid_gdf.copy()
    if g.crs is None:
        g = g.set_crs("EPSG:4326")
    g4326 = g.to_crs("EPSG:4326")
    g3857 = g4326.to_crs("EPSG:3857")
    cent_3857 = g3857.geometry.centroid
    cent_4326 = gpd.GeoSeries(cent_3857, crs="EPSG:3857").to_crs("EPSG:4326")
    return cent_4326.y.values.astype(np.float64), cent_4326.x.values.astype(np.float64)


def nearest_index_1d(arr, values):
    """Nearest index in 1D coordinate array for each value."""
    arr = np.asarray(arr)
    values = np.asarray(values)
    # brute force (safe for these sizes)
    idx = np.abs(arr.reshape(-1, 1) - values.reshape(1, -1)).argmin(axis=0)
    return idx.astype(np.int32)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--grid", required=True, help="Grid polygons file (gpkg/shp/geojson) with cell_id.")
    ap.add_argument("--nc", required=True, help="Sample ERA5-Land NetCDF (e.g., one month).")
    ap.add_argument("--outdir", required=True, help="Output folder for diagnostics.")
    ap.add_argument("--zone", default=None, help="Optional zone raster tif for zonal approach diagnostics.")
    ap.add_argument("--time_dim", default=TIME_DIM_DEFAULT, help="Time dimension name (default: valid_time).")
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    report = {
        "inputs": {
            "grid": args.grid,
            "nc": args.nc,
            "zone": args.zone,
            "time_dim": args.time_dim
        }
    }

    # -----------------------------
    # 1) Load grid + basic checks
    # -----------------------------
    grid = gpd.read_file(args.grid)
    if "cell_id" not in grid.columns:
        raise ValueError("Grid file must contain 'cell_id' column.")
    grid = grid[["cell_id", "geometry"]].copy()
    grid["cell_id"] = grid["cell_id"].astype(int)
    report["grid"] = {
        "n_cells": int(len(grid)),
        "crs": str(grid.crs),
        "bounds": [float(x) for x in grid.total_bounds],
        "cell_id_min": int(grid["cell_id"].min()),
        "cell_id_max": int(grid["cell_id"].max()),
        "cell_id_unique": int(grid["cell_id"].nunique()),
        "cell_id_duplicates": int(grid.duplicated(["cell_id"]).sum()),
        "geometry_types": grid.geometry.geom_type.value_counts().to_dict(),
    }

    # centroid coords
    cell_lats, cell_lons = compute_centroids_latlon(grid)
    cent_df = pd.DataFrame({"cell_id": grid["cell_id"].values, "lat": cell_lats, "lon": cell_lons})
    cent_df.to_csv(os.path.join(args.outdir, "grid_centroids.csv"), index=False)

    # -----------------------------
    # 2) Load netcdf + coord checks
    # -----------------------------
    ds = xr.open_dataset(args.nc)

    lat_name = find_coord_name(ds, LAT_NAMES)
    lon_name = find_coord_name(ds, LON_NAMES)
    if lat_name is None or lon_name is None:
        raise ValueError(f"Could not find latitude/longitude coords in dataset. Found coords: {list(ds.coords)}")

    time_dim = args.time_dim
    if time_dim not in ds.dims and time_dim not in ds.coords:
        # attempt guess
        # common alt: "time"
        if "time" in ds.dims or "time" in ds.coords:
            time_dim = "time"
        else:
            raise ValueError(f"Time dim '{args.time_dim}' not found. Dims: {list(ds.dims)}")

    report["netcdf"] = {
        "dims": {k: int(v) for k, v in ds.dims.items()},
        "coords": list(ds.coords),
        "data_vars": list(ds.data_vars),
        "lat_name": lat_name,
        "lon_name": lon_name,
        "time_dim_used": time_dim
    }

    # Check expected vars
    missing_vars = [v for v in VARS_EXPECTED if v not in ds.data_vars]
    report["netcdf"]["missing_expected_vars"] = missing_vars

    # Coordinate monotonicity / orientation
    lat_vals = ds[lat_name].values
    lon_vals = ds[lon_name].values
    report["coords"] = {
        "lat_min": float(np.min(lat_vals)),
        "lat_max": float(np.max(lat_vals)),
        "lon_min": float(np.min(lon_vals)),
        "lon_max": float(np.max(lon_vals)),
        "lat_descending": bool(lat_vals[0] > lat_vals[-1]),
        "lon_descending": bool(lon_vals[0] > lon_vals[-1]),
        "lat_step_abs": float(np.abs(lat_vals[1] - lat_vals[0])) if len(lat_vals) > 1 else None,
        "lon_step_abs": float(np.abs(lon_vals[1] - lon_vals[0])) if len(lon_vals) > 1 else None,
    }

    # -----------------------------
    # 3) Variable NaN diagnostics
    # -----------------------------
    var_reports = {}
    for v in VARS_EXPECTED:
        if v in ds.data_vars:
            var_reports[v] = describe_da(ds[v], time_dim, lat_name, lon_name)
    report["variables"] = var_reports

    # Save a compact table
    rows = []
    for v, r in var_reports.items():
        rows.append({
            "var": v,
            "dtype": r["dtype"],
            "nan_frac_overall": r["nan_frac_overall"],
            "nan_frac_t0": r.get("nan_frac_t0", np.nan),
            "min_finite": r["min_finite"],
            "max_finite": r["max_finite"]
        })
    pd.DataFrame(rows).to_csv(os.path.join(args.outdir, "netcdf_variable_nan_summary.csv"), index=False)

    # -----------------------------
    # 4) Spatial mask consistency across variables + time
    # -----------------------------
    # Use t2m as reference if available
    mask_checks = {}
    if "t2m" in ds.data_vars:
        t2m = ds["t2m"]
        for dim in ["number", "expver"]:
            if dim in t2m.dims:
                t2m = t2m.isel({dim: 0})
        # compare NaN mask at several times
        T = t2m.sizes[time_dim]
        idxs = np.unique(np.linspace(0, T - 1, num=min(6, T), dtype=int))
        masks = []
        for i in idxs:
            m = np.isfinite(t2m.isel({time_dim: i}).values)
            masks.append(m)
        # fraction of grid points that flip validity across sampled times
        stacked = np.stack(masks, axis=0)  # (k, lat, lon)
        ever_valid = stacked.any(axis=0)
        ever_invalid = (~stacked).any(axis=0)
        flips = (ever_valid & ever_invalid)
        mask_checks["t2m_mask_time_samples"] = {
            "sample_indices": idxs.tolist(),
            "valid_frac_each_sample": [float(m.mean()) for m in masks],
            "flip_frac_gridpoints": float(flips.mean()),
            "ever_valid_frac_gridpoints": float(ever_valid.mean()),
        }

        # Compare masks across variables at t0
        base = np.isfinite(t2m.isel({time_dim: 0}).values)
        for v in ["d2m", "u10", "v10"]:
            if v in ds.data_vars:
                vv = ds[v]
                for dim in ["number", "expver"]:
                    if dim in vv.dims:
                        vv = vv.isel({dim: 0})
                m2 = np.isfinite(vv.isel({time_dim: 0}).values)
                mask_checks[f"mask_match_t0_t2m_vs_{v}"] = float((base == m2).mean())

    report["mask_checks"] = mask_checks

    # Optional plot: spatial valid mask for t2m at t0
    if HAS_PLT and "t2m" in ds.data_vars:
        t2m = ds["t2m"]
        for dim in ["number", "expver"]:
            if dim in t2m.dims:
                t2m = t2m.isel({dim: 0})
        valid_mask = np.isfinite(t2m.isel({time_dim: 0}).values)
        plt.figure(figsize=(7, 5))
        plt.imshow(valid_mask, interpolation="nearest")
        plt.title("ERA5-Land valid mask (t2m at first timestep): True=valid")
        plt.axis("off")
        plt.tight_layout()
        plt.savefig(os.path.join(args.outdir, "era5_valid_mask_t2m_t0.png"), dpi=200)
        plt.close()

    # -----------------------------
    # 5) Diagnose centroid NN mapping → NaNs
    # -----------------------------
    # Compute nearest indices for each centroid
    lat_idx = nearest_index_1d(lat_vals, cell_lats)
    lon_idx = nearest_index_1d(lon_vals, cell_lons)

    map_df = pd.DataFrame({
        "cell_id": grid["cell_id"].values,
        "cell_lat": cell_lats,
        "cell_lon": cell_lons,
        "era_lat_idx": lat_idx,
        "era_lon_idx": lon_idx,
        "era_lat": lat_vals[lat_idx],
        "era_lon": lon_vals[lon_idx],
    })

    # Check NaN at those nearest points for each variable at time 0
    for v in VARS_EXPECTED:
        if v in ds.data_vars:
            da = ds[v]
            for dim in ["number", "expver"]:
                if dim in da.dims:
                    da = da.isel({dim: 0})
            da0 = da.isel({time_dim: 0}).values
            map_df[f"{v}_isnan_t0_at_nn"] = np.isnan(da0[lat_idx, lon_idx])

    # How many centroids map to NaN for t2m at t0?
    if "t2m_isnan_t0_at_nn" in map_df.columns:
        report["nn_sampling"] = {
            "centroids_mapping_to_nan_t2m_t0": int(map_df["t2m_isnan_t0_at_nn"].sum()),
            "centroids_mapping_to_valid_t2m_t0": int((~map_df["t2m_isnan_t0_at_nn"]).sum()),
        }

    map_df.to_csv(os.path.join(args.outdir, "centroid_nn_mapping_nan_flags.csv"), index=False)

    # Optional plot: scatter of centroids that map to NaN (in lat/lon)
    if HAS_PLT and "t2m_isnan_t0_at_nn" in map_df.columns:
        plt.figure(figsize=(7, 7))
        ok = ~map_df["t2m_isnan_t0_at_nn"]
        bad = map_df["t2m_isnan_t0_at_nn"]
        plt.scatter(map_df.loc[ok, "cell_lon"], map_df.loc[ok, "cell_lat"], s=3)
        plt.scatter(map_df.loc[bad, "cell_lon"], map_df.loc[bad, "cell_lat"], s=8)
        plt.title("Grid centroids mapped to ERA5 NN point: NaN vs valid (t2m, t0)")
        plt.xlabel("lon")
        plt.ylabel("lat")
        plt.tight_layout()
        plt.savefig(os.path.join(args.outdir, "centroids_nan_vs_valid.png"), dpi=200)
        plt.close()

    # -----------------------------
    # 6) Diagnose after daily aggregation (do NaNs persist?)
    # -----------------------------
    # compute daily aggregates for this ONE month file and check missing fractions
    daily_report = {}
    if all(v in ds.data_vars for v in VARS_EXPECTED):
        tmaxC, rhmin, wmax = daily_agg_simple(ds, time_dim, lat_name, lon_name)

        daily_report["tmaxC_nan_frac_overall"] = float(np.isnan(tmaxC.values).mean())
        daily_report["rhmin_nan_frac_overall"] = float(np.isnan(rhmin.values).mean())
        daily_report["wmax_nan_frac_overall"]  = float(np.isnan(wmax.values).mean())

        # Sample those daily fields at centroid NN indices (isel) for the month
        # (this mirrors the NN approach but shows the NaN problem clearly)
        tmax_nn = tmaxC.isel(
            {lat_name: xr.DataArray(lat_idx, dims="cell"), lon_name: xr.DataArray(lon_idx, dims="cell")}
        )
        rhm_nn = rhmin.isel(
            {lat_name: xr.DataArray(lat_idx, dims="cell"), lon_name: xr.DataArray(lon_idx, dims="cell")}
        )
        wmx_nn = wmax.isel(
            {lat_name: xr.DataArray(lat_idx, dims="cell"), lon_name: xr.DataArray(lon_idx, dims="cell")}
        )

        daily_report["tmaxC_nn_nan_frac"] = float(np.isnan(tmax_nn.values).mean())
        daily_report["rhmin_nn_nan_frac"] = float(np.isnan(rhm_nn.values).mean())
        daily_report["wmax_nn_nan_frac"]  = float(np.isnan(wmx_nn.values).mean())

        # Per-cell NaN fraction across days in this month
        per_cell = pd.DataFrame({
            "cell_id": grid["cell_id"].values,
            "tmax_nan_frac_month": np.isnan(tmax_nn.values).mean(axis=0),
            "rhmin_nan_frac_month": np.isnan(rhm_nn.values).mean(axis=0),
            "wmax_nan_frac_month": np.isnan(wmx_nn.values).mean(axis=0),
        })
        per_cell.to_csv(os.path.join(args.outdir, "per_cell_nan_frac_after_dailyagg_month.csv"), index=False)

    report["daily_agg"] = daily_report

    # -----------------------------
    # 7) Optional zone raster diagnostics
    # -----------------------------
    if args.zone:
        if not HAS_RIO:
            report["zone_raster"] = {"error": "rasterio not installed in this environment"}
        else:
            with rasterio.open(args.zone) as src:
                zone = src.read(1)
                nodata = src.nodata
                zone_report = {
                    "path": args.zone,
                    "shape": list(zone.shape),
                    "crs": str(src.crs),
                    "transform": str(src.transform),
                    "nodata": nodata,
                    "inside_pixel_count": int(np.sum(zone != nodata)),
                    "total_pixel_count": int(zone.size),
                    "inside_fraction": float(np.mean(zone != nodata)),
                }
                uniq = np.unique(zone[zone != nodata]).astype(int)
                zone_report["unique_cell_ids_in_raster"] = int(len(uniq))
                zone_report["unique_cell_ids_sample"] = uniq[:20].tolist()
                # cell_ids missing in raster
                all_ids = set(grid["cell_id"].tolist())
                present_ids = set(uniq.tolist())
                missing_ids = sorted(all_ids - present_ids)
                zone_report["missing_cell_ids_zero_pixels"] = int(len(missing_ids))

                pd.Series(missing_ids, name="cell_id").to_csv(
                    os.path.join(args.outdir, "zone_raster_missing_cell_ids.csv"), index=False
                )

                report["zone_raster"] = zone_report

                if HAS_PLT:
                    plt.figure(figsize=(7, 5))
                    plt.imshow(zone != nodata, interpolation="nearest")
                    plt.title("Zone raster coverage mask (True = inside any cell)")
                    plt.axis("off")
                    plt.tight_layout()
                    plt.savefig(os.path.join(args.outdir, "zone_raster_coverage_mask.png"), dpi=200)
                    plt.close()

    # -----------------------------
    # 8) Save master report
    # -----------------------------
    with open(os.path.join(args.outdir, "diagnostic_report.json"), "w") as f:
        json.dump(report, f, indent=2)

    # Print the key conclusions in terminal
    print("\n=== KEY DIAGNOSTIC SUMMARY ===")
    print("Grid cells:", report["grid"]["n_cells"], " CRS:", report["grid"]["crs"])
    print("NetCDF dims:", report["netcdf"]["dims"])
    print("Missing expected vars:", report["netcdf"]["missing_expected_vars"])

    if "t2m" in report["variables"]:
        print("t2m NaN fraction overall:", report["variables"]["t2m"]["nan_frac_overall"])
        print("t2m NaN fraction at t0:", report["variables"]["t2m"].get("nan_frac_t0", None))

    if "nn_sampling" in report:
        print("Centroids mapping to NaN at NN point (t2m, t0):",
              report["nn_sampling"]["centroids_mapping_to_nan_t2m_t0"])

    if report.get("daily_agg"):
        print("Daily agg overall NaN fractions:",
              {k: report["daily_agg"][k] for k in report["daily_agg"]})

    if args.zone and "zone_raster" in report and "missing_cell_ids_zero_pixels" in report["zone_raster"]:
        print("Zone raster missing cell_ids (zero pixels):", report["zone_raster"]["missing_cell_ids_zero_pixels"])

    print("\nOutputs written to:", args.outdir)
    print(" - diagnostic_report.json")
    print(" - netcdf_variable_nan_summary.csv")
    print(" - centroid_nn_mapping_nan_flags.csv")
    print(" - per_cell_nan_frac_after_dailyagg_month.csv (if vars present)")
    if HAS_PLT:
        print(" - png plots (if matplotlib available)")


if __name__ == "__main__":
    main()

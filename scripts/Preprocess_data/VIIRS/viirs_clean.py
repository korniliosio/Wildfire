import geopandas as gpd
import pandas as pd
"""
Clean VIIRS fire data for Greece.
"""

in_path = "thesis_data/VIIRS/labels/VIIRS_greece.gpkg"
out_path = "thesis_data/VIIRS/labels/VIIRS_greece_clean.gpkg"

fires_raw = gpd.read_file(in_path)

fires_clean = fires_raw[["ACQ_DATE", "CONFIDENCE", "geometry"]].copy()
fires_clean["date"] = pd.to_datetime(fires_clean["ACQ_DATE"], errors="coerce")

# save as NEW file (original untouched)
fires_clean.to_file(out_path, driver="GPKG")

print("Saved:", out_path)
print("Rows:", len(fires_clean), " | Missing dates:", fires_clean["date"].isna().sum())
print("Date range:", fires_clean["date"].min(), "→", fires_clean["date"].max())

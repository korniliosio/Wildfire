import geopandas as gpd
"""
Filter VIIRS fire data to the date range 2015-2024.
"""

in_path = "thesis_data/VIIRS/labels/VIIRS_greece_clean.gpkg"
out_path = "thesis_data/VIIRS/labels/VIIRS_greece_clean_2015_2024.gpkg"

fires = gpd.read_file(in_path)

fires_2015_2024 = fires[
    (fires["date"] >= "2015-01-01") & (fires["date"] <= "2024-12-31")
].copy()

fires_2015_2024.to_file(out_path, driver="GPKG")

print("Saved:", out_path)
print("Rows:", len(fires_2015_2024))
print("Date range:", fires_2015_2024["date"].min(), "→", fires_2015_2024["date"].max())

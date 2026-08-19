import json
from pathlib import Path
import geopandas as gpd

input_path = "thesis_data/VIIRS/labels/VIIRS_fires_with_cell_id.gpkg"
output_dir = Path("thesis_data/web_exports/viirs")
output_dir.mkdir(parents=True, exist_ok=True)

gdf = gpd.read_file(input_path)
gdf = gdf.to_crs(epsg=4326)

# keep prediction-period only
gdf["date_str"] = gdf["date"].dt.strftime("%Y-%m-%d")
gdf = gdf[(gdf["date_str"] >= "2023-01-01") & (gdf["date_str"] <= "2024-12-30")].copy()

for date_str, day in gdf.groupby("date_str"):
    records = []

    for _, row in day.iterrows():
        records.append({
            "cell_id": int(row["cell_id"]) if row["cell_id"] == row["cell_id"] else None,
            "lon": float(row.geometry.x),
            "lat": float(row.geometry.y),
            "confidence": str(row["CONFIDENCE"]),
        })

    with open(output_dir / f"{date_str}.json", "w", encoding="utf-8") as f:
        json.dump(records, f)

print(f"Exported {gdf['date_str'].nunique()} VIIRS daily files")
print(f"Total detections exported: {len(gdf)}")
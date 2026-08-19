#!/usr/bin/env python3
"""
Extract Greece from the Eurostat/GISCO CNTR_RG shapefile and write a Greece-only shapefile.

Assumptions for this dataset:
- Greece has CNTR_ID == "EL" (Eurostat code)
Input:  thesis_data/bounds/CNTR_RG_01M_2024_4326.shp
Output: thesis_data/bounds/greece_4326.shp (+ sidecar files)
"""

from pathlib import Path
import sys
import geopandas as gpd



def main() -> int:
    in_path = Path("thesis_data/bounds/CNTR_RG_01M_2024_4326.shp")
    out_path = Path("thesis_data/bounds/greece_4326.shp")

    if not in_path.exists():
        print(f"ERROR: Input shapefile not found: {in_path}", file=sys.stderr)
        return 1

    gdf = gpd.read_file(in_path)

    if "CNTR_ID" not in gdf.columns:
        print(f"ERROR: 'CNTR_ID' column not found. Columns are: {list(gdf.columns)}", file=sys.stderr)
        return 2

    greece = gdf[gdf["CNTR_ID"] == "EL"].copy()

    if greece.empty:
        # Fallbacks if your file uses different coding/fields
        for field, value in [("ISO3_CODE", "GRC"), ("CNTR_CODE", "EL"), ("CNTR_NAME", "Greece")]:
            if field in gdf.columns:
                greece = gdf[gdf[field] == value].copy()
                if not greece.empty:
                    print(f"NOTE: Greece found using {field} == {value}")
                    break

    if greece.empty:
        print(
            "ERROR: Could not find Greece. Try printing unique codes:\n"
            "  print(sorted(gdf['CNTR_ID'].unique()))",
            file=sys.stderr,
        )
        return 3

    # Ensure output folder exists
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Optional: ensure a valid CRS is carried through (should be EPSG:4326 in your file)
    if greece.crs is None and gdf.crs is not None:
        greece = greece.set_crs(gdf.crs)

    greece.to_file(out_path)
    print(f"Saved: {out_path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

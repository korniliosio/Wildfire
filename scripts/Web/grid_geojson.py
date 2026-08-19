from pathlib import Path
import geopandas as gpd

# -----------------------
# INPUT / OUTPUT PATHS
# -----------------------
input_path = "thesis_data/grid/greece_grid_10km_4326.gpkg"
output_path = Path("thesis_data/web_exports/grid.geojson")

# -----------------------
# LOAD GRID
# -----------------------
gdf = gpd.read_file(input_path)

# -----------------------
# BASIC INSPECTION
# -----------------------
print("Grid shape:", gdf.shape)
print("\nColumns:")
print(gdf.columns.tolist())

print("\nCRS:")
print(gdf.crs)

print("\nGeometry type counts:")
print(gdf.geometry.geom_type.value_counts())

# -----------------------
# KEEP ONLY NEEDED COLUMNS
# -----------------------
if "cell_id" not in gdf.columns:
    raise ValueError("cell_id column not found in grid file.")

gdf = gdf[["cell_id", "geometry"]].copy()

# -----------------------
# OPTIONAL: SORT FOR CONSISTENCY
# -----------------------
gdf = gdf.sort_values("cell_id").reset_index(drop=True)

# -----------------------
# OPTIONAL: ENSURE CRS IS EPSG:4326
# -----------------------
if gdf.crs is None:
    raise ValueError("Grid CRS is missing.")
if gdf.crs.to_epsg() != 4326:
    gdf = gdf.to_crs(epsg=4326)

# -----------------------
# EXPORT TO GEOJSON
# -----------------------
output_path.parent.mkdir(exist_ok=True)
gdf.to_file(output_path, driver="GeoJSON")

print(f"\nSaved {output_path}")
print("Final shape:", gdf.shape)
print("Cell ID range:", gdf['cell_id'].min(), "to", gdf['cell_id'].max())
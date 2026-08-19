import geopandas as gpd

path = "thesis_data/VIIRS/labels/VIIRS_fires_with_cell_id.gpkg"

gdf = gpd.read_file(path)

print("Shape:", gdf.shape)
print("Columns:", gdf.columns.tolist())
print("CRS:", gdf.crs)
print("Geometry types:")
print(gdf.geometry.geom_type.value_counts())
print(gdf.head())
import geopandas as gpd
"""
Assign VIIRS fire points to grid cells by spatial join.
"""
# paths
fires_path = "thesis_data/VIIRS/labels/VIIRS_greece_clean_2015_2024.gpkg"
grid_path = "thesis_data/grid/greece_grid_10km_4326.gpkg"
out_path = "thesis_data/VIIRS/labels/VIIRS_fires_with_cell_id.gpkg"

# load data
fires = gpd.read_file(fires_path)
grid = gpd.read_file(grid_path)

# spatial join: assign cell_id to each fire
fires_with_cell = gpd.sjoin(
    fires,
    grid[["cell_id", "geometry"]],
    how="left",
    predicate="within"
)

# save as NEW file
fires_with_cell.to_file(out_path, driver="GPKG")

print("Saved:", out_path)
print("Total fires:", len(fires_with_cell))
print("Fires without cell_id:", fires_with_cell["cell_id"].isna().sum())
print(fires_with_cell[["date", "cell_id"]].head())

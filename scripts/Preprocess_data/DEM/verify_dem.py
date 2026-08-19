import rasterio
import geopandas as gpd

GRID_PATH = "thesis_data/grid/greece_grid_10km_4326.gpkg"

DEM_PATH = "thesis_data/dem/clipped-aligned/dem_data_clipped_aligned.tif"
SLOPE_PATH = "thesis_data/dem/clipped-aligned/slope_aligned.tif"
ASPECT_PATH = "thesis_data/dem/clipped-aligned/aspect_aligned.tif"

grid = gpd.read_file(GRID_PATH)
print("Grid CRS:", grid.crs)
print("Grid bounds:", grid.total_bounds)

def info(path):
    with rasterio.open(path) as src:
        print("\n===", path, "===")
        print("CRS:", src.crs)
        print("Bounds:", src.bounds)
        print("Width x Height:", src.width, "x", src.height)
        print("Res:", src.res)
        print("Transform:", src.transform)
        print("Nodata:", src.nodata)
        print("Dtype:", src.dtypes)
        print("Count:", src.count)

info(DEM_PATH)
info(SLOPE_PATH)
info(ASPECT_PATH)

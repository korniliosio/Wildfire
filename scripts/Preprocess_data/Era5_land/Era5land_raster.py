import os
import numpy as np
import geopandas as gpd
import xarray as xr
import rasterio
from rasterio.transform import from_origin
from rasterio.features import rasterize
from pyproj import Transformer

GRID_PATH = "thesis_data/grid/greece_grid_10km_4326.gpkg"
NC_SAMPLE = "thesis_data/era5land_hourly/raw/era5land_greece_2015_01.nc"
OUT_ZONE  = "thesis_data/features/grid_cell_id_zones_era5land.tif"

os.makedirs("thesis_data/features", exist_ok=True)

# 1) ERA5 grid
ds = xr.open_dataset(NC_SAMPLE, engine="netcdf4")
lat = ds["latitude"].values
lon = ds["longitude"].values

dlat = float(np.abs(lat[1] - lat[0]))
dlon = float(np.abs(lon[1] - lon[0]))
height, width = lat.shape[0], lon.shape[0]

north = float(lat.max()) + dlat / 2
west  = float(lon.min()) - dlon / 2
transform = from_origin(west, north, dlon, dlat)

# 2) Load grid polygons
grid = gpd.read_file(GRID_PATH)[["cell_id", "geometry"]].copy()
grid["cell_id"] = grid["cell_id"].astype(int)
grid = grid.set_crs("EPSG:4326", allow_override=True)

# 3) Buffer in meters using projected CRS
BUFFER_M = 1500   # try 1500m first; if still missing cells, increase to 2500m
grid_m = grid.to_crs("EPSG:3857")
grid_m["geometry"] = grid_m.geometry.buffer(BUFFER_M)

# back to 4326 for rasterize (because transform/crs are 4326)
grid_buf = grid_m.to_crs("EPSG:4326")

shapes = ((geom, cid) for geom, cid in zip(grid_buf.geometry, grid_buf.cell_id))

zone = rasterize(
    shapes=shapes,
    out_shape=(height, width),
    transform=transform,
    fill=-1,
    dtype="int32",
    all_touched=True
)

present_ids = np.unique(zone[zone != -1])
print("Unique cell_ids present in zone raster:", len(present_ids))
print("Total grid cells:", len(grid_buf))
print("Missing cell_ids (zero pixels):", len(grid_buf) - len(present_ids))
print("Pixels inside zones:", int((zone != -1).sum()), "out of", zone.size)

meta = {
    "driver": "GTiff",
    "height": height,
    "width": width,
    "count": 1,
    "dtype": "int32",
    "crs": "EPSG:4326",
    "transform": transform,
    "nodata": -1,
    "compress": "LZW"
}
with rasterio.open(OUT_ZONE, "w", **meta) as dst:
    dst.write(zone, 1)

print("Saved zone raster:", OUT_ZONE)

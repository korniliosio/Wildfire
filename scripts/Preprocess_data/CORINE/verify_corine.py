import rasterio
import numpy as np

FUEL_PATH = "thesis_data/corine_landcover/fuel/fuel_types_aligned.tif"

with rasterio.open(FUEL_PATH) as src:
    print("CRS:", src.crs)
    print("Bounds:", src.bounds)
    print("Resolution:", src.res)
    print("Shape:", src.width, "x", src.height)
    print("Nodata:", src.nodata)
    arr = src.read(1)

unique = np.unique(arr)
print("Unique fuel codes (sample):", unique[:20])
print("Total unique codes:", len(unique))

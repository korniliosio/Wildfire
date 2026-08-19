from pathlib import Path

import numpy as np
import rasterio

ROOT = Path("thesis_data")
IN_PATH = ROOT / "corine_landcover" / "clipped" / "corine_reprojected.tif"
OUT_PATH = ROOT / "corine_landcover" / "clipped" / "fuel_types.tif"


def main():
    print(f"Reading {IN_PATH}")
    with rasterio.open(IN_PATH) as src:
        profile = src.profile
        data = src.read(1)  # first (and only) band

    # Start with all zeros (= "other / no fuel")
    fuel = np.zeros_like(data, dtype=np.uint8)

    # 1: Urban (111–142)
    mask = (data >= 111) & (data <= 142)
    fuel[mask] = 1

    # 2: Agriculture (211–244)
    mask = (data >= 211) & (data <= 244)
    fuel[mask] = 2

    # 3: Grassland (231)
    mask = data == 231
    fuel[mask] = 3

    # 4: Shrubland (322, 323, 324)
    mask = np.isin(data, [322, 323, 324])
    fuel[mask] = 4

    # 5: Forest (311, 312, 313)
    mask = np.isin(data, [311, 312, 313])
    fuel[mask] = 5

    # 6: Bare / sparsely vegetated (321, 331–335)
    mask = np.isin(data, [321, 331, 332, 333, 334, 335])
    fuel[mask] = 6

    # 7: Wetlands (411–423)
    mask = (data >= 411) & (data <= 423)
    fuel[mask] = 7

    # 8: Water (511–523)
    mask = (data >= 511) & (data <= 523)
    fuel[mask] = 8

    # Update profile for uint8, 1 band
    profile.update(
        dtype=rasterio.uint8,
        count=1,
        nodata=0,  # 0 = "other / non-burnable"
    )

    print(f"Writing {OUT_PATH}")
    with rasterio.open(OUT_PATH, "w", **profile) as dst:
        dst.write(fuel, 1)

    print("Done.")


if __name__ == "__main__":
    main()

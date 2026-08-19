import os
import cdsapi
from calendar import monthrange

# Output folder
OUT_DIR = "thesis_data/era5land_hourly/raw"
os.makedirs(OUT_DIR, exist_ok=True)

# ERA5-Land hourly dataset on CDS
DATASET = "reanalysis-era5-land"

# Greece-ish bounding box (North, West, South, East) - padded a bit for islands
AREA = [41.8, 19.2, 34.6, 29.8]

VARIABLES = [
    "2m_temperature",
    "2m_dewpoint_temperature",
    "10m_u_component_of_wind",
    "10m_v_component_of_wind",
]

c = cdsapi.Client()

def download_month(year: int, month: int):
    days_in_month = monthrange(year, month)[1]
    target = os.path.join(OUT_DIR, f"era5land_greece_{year}_{month:02d}.nc")

    # Resume-safe: skip if file already exists and is non-trivial size
    if os.path.exists(target) and os.path.getsize(target) > 1_000_000:
        print(f"Skip (exists): {target}")
        return

    request = {
        "variable": VARIABLES,
        "year": str(year),
        "month": f"{month:02d}",
        "day": [f"{d:02d}" for d in range(1, days_in_month + 1)],
        "time": [f"{h:02d}:00" for h in range(0, 24)],
        "area": AREA,
        "format": "netcdf",
    }

    print(f"Downloading {year}-{month:02d} → {target}")
    c.retrieve(DATASET, request, target)
    print(f"Done: {target} ({os.path.getsize(target)/1e6:.1f} MB)")

for year in range(2015, 2025):
    for month in range(1, 13):
        download_month(year, month)

print("All downloads attempted.")

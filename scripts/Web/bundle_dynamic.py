from pathlib import Path
import json
import pandas as pd

# Code to bundle the dynamic data with predictions into daily JSON files for web use

# -----------------------
# INPUT / OUTPUT PATHS
# -----------------------
input_path = "thesis_data/FINAL_DATA/dynamic_data.parquet"
output_dir = Path("thesis_data/web_exports")
bundles_dir = output_dir / "bundles"

output_dir.mkdir(exist_ok=True)
bundles_dir.mkdir(exist_ok=True)

# -----------------------
# LOAD DATA
# -----------------------
df = pd.read_parquet(input_path)

# -----------------------
# KEEP ONLY DATES WITH PREDICTIONS
# -----------------------
df = df[df["p_fire_tomorrow"].notna()].copy()

# -----------------------
# FORMAT DATE FOR WEB USE
# -----------------------
df["date_str"] = df["date"].dt.strftime("%Y-%m-%d")

# -----------------------
# COLUMNS TO EXPORT IN EACH DAILY BUNDLE
# fuel_missing removed because it is now static
# -----------------------
bundle_cols = [
    "cell_id",
    "p_fire_tomorrow",
    "fire_tomorrow",
    "fire",
    "temp_daily_max_C",
    "rh_daily_min",
    "wind_daily_max",
]

# -----------------------
# EXPORT DAILY JSON FILES
# -----------------------
all_dates = sorted(df["date_str"].unique())

for date_str in all_dates:
    day_df = df.loc[df["date_str"] == date_str, bundle_cols].copy()
    day_df = day_df.sort_values("cell_id").reset_index(drop=True)

    out_path = bundles_dir / f"{date_str}.json"

    records = day_df.to_dict(orient="records")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(records, f)

    print(f"Saved {out_path} ({len(records)} rows)")

# -----------------------
# EXPORT DATE INDEX
# -----------------------
with open(output_dir / "dates.json", "w", encoding="utf-8") as f:
    json.dump(all_dates, f)

print(f"\nExported {len(all_dates)} daily bundle files.")
print(f"Date range: {all_dates[0]} to {all_dates[-1]}")
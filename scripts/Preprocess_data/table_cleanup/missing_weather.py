import pandas as pd

PARQUET_PATH = "thesis_data/model_table/model_table_nextday_with_fuel_2015_2024_slopev2.parquet"
OUT_PATH = "thesis_data/model_table/model_table_nextday_with_fuel_2015_2024_clean.parquet"

# Load
df = pd.read_parquet(PARQUET_PATH)

print("Initial rows:", len(df))

weather_cols = [
    "temp_daily_max_C",
    "rh_daily_min",
    "wind_daily_max",
]

# Count missing before
missing_before = df[weather_cols].isna().any(axis=1).sum()
print(f"Rows with missing weather: {missing_before} ({missing_before / len(df) * 100:.2f}%)")

# Drop rows with any missing weather
df_clean = df.dropna(subset=weather_cols).reset_index(drop=True)

print("Rows after dropping missing weather:", len(df_clean))
print("Dropped rows:", len(df) - len(df_clean))

# Sanity check
assert df_clean[weather_cols].isna().sum().sum() == 0

# Save
df_clean.to_parquet(OUT_PATH)
print("Saved:", OUT_PATH)

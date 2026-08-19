import pandas as pd
import numpy as np
import os
"""Final preprocessing of model table before modeling."""

IN_PATH = "thesis_data/model_table/model_table_nextday_2015_2024.parquet"
OUT_PATH = "thesis_data/model_table/model_table_nextday_ready_2015_2024.parquet"

df = pd.read_parquet(IN_PATH)

# Fill flat-terrain aspect components with 0
df["northness_mean"] = df["northness_mean"].fillna(0.0)
df["eastness_mean"] = df["eastness_mean"].fillna(0.0)

# Optional sanity checks (print only)
print("Temp range:", df["temp_daily_max_C"].min(), "→", df["temp_daily_max_C"].max())
print("RH range:", df["rh_daily_min"].min(), "→", df["rh_daily_min"].max())
print("Wind range:", df["wind_daily_max"].min(), "→", df["wind_daily_max"].max())
print("Slope range:", df["slope_mean"].min(), "→", df["slope_mean"].max())

os.makedirs("thesis_data/model", exist_ok=True)
df.to_parquet(OUT_PATH, index=False)

print("Saved:", OUT_PATH)
print("Rows:", len(df))
print("Fire rate:", float(df["fire"].mean()))
print(df.head())

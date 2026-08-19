import pandas as pd
import os
"""Create next-day fire occurrence target variable."""

IN_PATH  = "thesis_data/model_table/model_table_ready_2015_2024.parquet"
OUT_PATH = "thesis_data/model_table/model_table_nextday_2015_2024.parquet"

df = pd.read_parquet(IN_PATH)

# ensure correct ordering
df = df.sort_values(["cell_id", "date"])

# next-day target per cell
df["fire_tomorrow"] = (
    df.groupby("cell_id")["fire"]
      .shift(-1)
)

# drop last day per cell (no tomorrow)
df = df.dropna(subset=["fire_tomorrow"]).copy()
df["fire_tomorrow"] = df["fire_tomorrow"].astype("int8")

os.makedirs("thesis_data/model", exist_ok=True)
df.to_parquet(OUT_PATH, index=False)

print("Saved:", OUT_PATH)
print("Rows:", len(df))
print("Fire tomorrow count:", int(df["fire_tomorrow"].sum()))
print("Fire tomorrow rate:", float(df["fire_tomorrow"].mean()))
print(df[["cell_id", "date", "fire", "fire_tomorrow"]].head(10))

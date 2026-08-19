import pandas as pd
from pathlib import Path

IN_PATH = "thesis_data/model_table/model_table_nextday_2015_2024_final.parquet"
OUT_DIR = Path("thesis_data/model_table/splits")

OUT_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_parquet(IN_PATH)
df["date"] = pd.to_datetime(df["date"])
df["year"] = df["date"].dt.year

train_years = list(range(2015, 2022))
val_years   = [2022]
test_years  = [2023, 2024]

train_df = df[df["year"].isin(train_years)].copy()
val_df   = df[df["year"].isin(val_years)].copy()
test_df  = df[df["year"].isin(test_years)].copy()

print("Split sizes:")
print("Train:", len(train_df))
print("Val:  ", len(val_df))
print("Test: ", len(test_df))

print("Train fire_tomorrow rate:", train_df["fire_tomorrow"].mean())
print("Val fire_tomorrow rate:  ", val_df["fire_tomorrow"].mean())
print("Test fire_tomorrow rate: ", test_df["fire_tomorrow"].mean())

# Save
train_df.to_parquet(OUT_DIR / "train.parquet")
val_df.to_parquet(OUT_DIR / "val.parquet")
test_df.to_parquet(OUT_DIR / "test.parquet")

print("Saved splits to:", OUT_DIR)

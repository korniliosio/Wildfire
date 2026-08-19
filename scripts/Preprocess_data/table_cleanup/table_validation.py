import pandas as pd

PATH = "thesis_data/model_table/model_table_nextday_2015_2024_final.parquet"

df = pd.read_parquet(PATH)

print("=== BASIC SHAPE ===")
print("Rows:", len(df))
print("Unique cells:", df["cell_id"].nunique())
print("Date range:", df["date"].min(), "→", df["date"].max())

# --------------------------------------------------
# 1) Uniqueness: exactly one row per (cell_id, date)
# --------------------------------------------------
print("\n=== UNIQUENESS CHECK ===")
dups = df.duplicated(["cell_id", "date"]).sum()
print("Duplicate (cell_id, date) rows:", dups)
assert dups == 0, "Duplicates found!"

# --------------------------------------------------
# 2) Temporal consistency per cell
# --------------------------------------------------
print("\n=== TEMPORAL CONSISTENCY ===")
bad_cells = (
    df.sort_values(["cell_id", "date"])
      .groupby("cell_id")["date"]
      .apply(lambda s: not s.is_monotonic_increasing)
)
n_bad = int(bad_cells.sum())
print("Cells with non-monotonic dates:", n_bad)
assert n_bad == 0, "Temporal order broken for some cells!"

# --------------------------------------------------
# 3) Feature completeness (NO NaNs in predictors)
# --------------------------------------------------
print("\n=== MISSING VALUE CHECK ===")
feature_cols = [
    "temp_daily_max_C",
    "rh_daily_min",
    "wind_daily_max",
    "elev_mean",
    "northness_mean",
    "eastness_mean",
    "slope_mean",
]

fuel_cols = [c for c in df.columns if c.startswith("fuel_")]

all_features = feature_cols + fuel_cols

missing = df[all_features].isna().sum()
print(missing[missing > 0])

assert missing.sum() == 0, "Missing values in features!"

# --------------------------------------------------
# 4) Target sanity
# --------------------------------------------------
print("\n=== TARGET CHECK ===")
assert set(df["fire"].unique()) <= {0, 1}, "fire not binary!"
assert set(df["fire_tomorrow"].unique()) <= {0, 1}, "fire_tomorrow not binary!"

rate = df["fire_tomorrow"].mean()
print("fire_tomorrow rate:", rate)
assert 0 < rate < 0.05, "Suspicious fire_tomorrow rate!"

# --------------------------------------------------
# 5) Feature range sanity (quick)
# --------------------------------------------------
print("\n=== RANGE SANITY ===")
ranges = {
    "temp_daily_max_C": (-30, 60),
    "rh_daily_min": (0, 100),
    "wind_daily_max": (0, 60),
    "slope_mean": (0, 90),
}

for col, (lo, hi) in ranges.items():
    bad = ((df[col] < lo) | (df[col] > hi)).sum()
    print(f"{col}: out-of-range rows:", int(bad))
    assert bad == 0, f"{col} out of expected range!"

# --------------------------------------------------
# 6) Fuel fractions sanity
# --------------------------------------------------
print("\n=== FUEL FRACTION CHECK ===")
fuel_sum = df[fuel_cols].sum(axis=1)
bad_fuel = ((fuel_sum < 0.95) | (fuel_sum > 1.05)).sum()
print("Fuel sum outside [0.95, 1.05]:", int(bad_fuel))
assert bad_fuel == 0, "Fuel fractions do not sum to ~1!"

# --------------------------------------------------
print("\n✅ DATASET IS READY FOR SPLITTING AND MODELING")

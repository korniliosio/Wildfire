import pandas as pd

# Code to split the master dataframe into static and dynamic tables
# and merge predictions into the dynamic table

master_df = pd.read_parquet("thesis_data/model_table/model_table_nextday_2015_2024_final.parquet")
pred_df = pd.read_parquet("thesis_data/model/results/xgb_predictions.parquet")


static_vars = [
    "cell_id",
    "elev_mean",
    "northness_mean",
    "eastness_mean",
    "slope_mean",
    "fuel_urban_frac",
    "fuel_agriculture_frac",
    "fuel_grass_frac",
    "fuel_shrub_frac",
    "fuel_forest_frac",
    "fuel_nonburnable_frac",
    "fuel_missing"
]

# -----------------------
# DEFINE DYNAMIC VARIABLES
# -----------------------
dynamic_vars = [
    "fire",
    "temp_daily_max_C",
    "rh_daily_min",
    "wind_daily_max",
    "fire_tomorrow"
]


check = master_df.groupby("cell_id")[static_vars[1:]].nunique()
print("Max unique values per static column:")
print(check.max())


static_df = master_df[static_vars].drop_duplicates().sort_values("cell_id").reset_index(drop=True)


dynamic_df = master_df[["cell_id", "date"] + dynamic_vars].copy()


pred_df = pred_df[["cell_id", "date", "p_fire_tomorrow"]].copy()


dynamic_df = dynamic_df.merge(
    pred_df,
    on=["cell_id", "date"],
    how="left",
    validate="one_to_one"
)


print("\nStatic table shape:", static_df.shape)
print("Dynamic table shape:", dynamic_df.shape)

print("\nPrediction coverage:")
print(dynamic_df["p_fire_tomorrow"].notna().value_counts())

print("\nDate range in dynamic table:")
print(dynamic_df["date"].min(), "to", dynamic_df["date"].max())

print("\nDate range with predictions:")
pred_dates = dynamic_df.loc[dynamic_df["p_fire_tomorrow"].notna(), "date"]
print(pred_dates.min(), "to", pred_dates.max())


static_df.to_parquet("thesis_data/FINAL_DATA/static_data.parquet", index=False)
dynamic_df.to_parquet("thesis_data/FINAL_DATA/dynamic_data.parquet", index=False)

print(f"\nStatic data size: {static_df.memory_usage(deep=True).sum() / 1e6:.2f} MB")
print(f"Dynamic data size: {dynamic_df.memory_usage(deep=True).sum() / 1e6:.2f} MB")
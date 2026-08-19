import pandas as pd

MODEL_TABLE = "thesis_data/model_table/model_table_nextday_2015_2024_final.parquet"

df = pd.read_parquet(MODEL_TABLE)

weather_vars = [
    "temp_daily_max_C",
    "rh_daily_min",
    "wind_daily_max",
]

terrain_vars = [
    "elev_mean",
    "northness_mean",
    "eastness_mean",
    "slope_mean",
]

fuel_vars = [
    "fuel_urban_frac",
    "fuel_agriculture_frac",
    "fuel_grass_frac",
    "fuel_shrub_frac",
    "fuel_forest_frac",
    "fuel_nonburnable_frac",
]

target = "fire_tomorrow"

stats = {
    "Study period": f"{df['date'].min().date()} to {df['date'].max().date()}",
    "Number of analysis cells": df["cell_id"].nunique(),
    "Number of dates": df["date"].nunique(),
    "Total observations": len(df),
    "Temporal resolution": "Daily",
    "Spatial resolution": "10 km × 10 km",
    "Weather variables": len(weather_vars),
    "Terrain variables": len(terrain_vars),
    "Fuel variables": len(fuel_vars),
    "Total predictor variables": len(weather_vars + terrain_vars + fuel_vars),
    "Target variable": target,
    "Fire tomorrow count": int(df[target].sum()),
    "No fire tomorrow count": int((df[target] == 0).sum()),
    "Positive class rate (%)": round(df[target].mean() * 100, 4),
}

summary = pd.DataFrame(
    [{"Statistic": key, "Value": value} for key, value in stats.items()]
)

print(summary.to_string(index=False))

summary.to_csv("thesis/figures/final_dataset_statistics.csv", index=False)

print("\nSaved: thesis/figures/final_dataset_statistics.csv")
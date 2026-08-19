from pathlib import Path
import json

metadata = {
    "app": {
        "title": "Wildfire Risk Explorer",
        "default_date": "2023-01-01",
        "default_layer": "p_fire_tomorrow"
    },
    "layers": [
        {
            "id": "p_fire_tomorrow",
            "label": "Predicted Fire Risk",
            "source": "dynamic",
            "temporal": True,
            "unit": "probability",
            "legend_type": "sequential",
            "domain": [0.0, 1.0]
        },
        {
            "id": "temp_daily_max_C",
            "label": "Maximum Temperature",
            "source": "dynamic",
            "temporal": True,
            "unit": "°C",
            "legend_type": "sequential",
            "domain": [-10.0, 50.0]
        },
        {
            "id": "rh_daily_min",
            "label": "Minimum Relative Humidity",
            "source": "dynamic",
            "temporal": True,
            "unit": "%",
            "legend_type": "sequential",
            "domain": [0.0, 100.0]
        },
        {
            "id": "wind_daily_max",
            "label": "Maximum Wind Speed",
            "source": "dynamic",
            "temporal": True,
            "unit": "m/s",
            "legend_type": "sequential",
            "domain": [0.0, 30.0]
        },
        {
            "id": "slope_mean",
            "label": "Slope",
            "source": "static",
            "temporal": False,
            "unit": "degrees",
            "legend_type": "sequential",
            "domain": [0.0, 90.0]
        },
        {
            "id": "elev_mean",
            "label": "Elevation",
            "source": "static",
            "temporal": False,
            "unit": "m",
            "legend_type": "sequential",
            "domain": [0.0, 3000.0]
        },
        {
            "id": "fuel_urban_frac",
            "label": "Urban Fraction",
            "source": "static",
            "temporal": False,
            "unit": "fraction",
            "legend_type": "sequential",
            "domain": [0.0, 1.0]
        },
        {
            "id": "fuel_agriculture_frac",
            "label": "Agriculture Fraction",
            "source": "static",
            "temporal": False,
            "unit": "fraction",
            "legend_type": "sequential",
            "domain": [0.0, 1.0]
        },
        {
            "id": "fuel_grass_frac",
            "label": "Grass Fraction",
            "source": "static",
            "temporal": False,
            "unit": "fraction",
            "legend_type": "sequential",
            "domain": [0.0, 1.0]
        },
        {
            "id": "fuel_shrub_frac",
            "label": "Shrub Fraction",
            "source": "static",
            "temporal": False,
            "unit": "fraction",
            "legend_type": "sequential",
            "domain": [0.0, 1.0]
        },
        {
            "id": "fuel_forest_frac",
            "label": "Forest Fraction",
            "source": "static",
            "temporal": False,
            "unit": "fraction",
            "legend_type": "sequential",
            "domain": [0.0, 1.0]
        },
        {
            "id": "fuel_nonburnable_frac",
            "label": "Non-burnable Fraction",
            "source": "static",
            "temporal": False,
            "unit": "fraction",
            "legend_type": "sequential",
            "domain": [0.0, 1.0]
        },
        {
            "id": "fuel_missing",
            "label": "Fuel Missing Indicator",
            "source": "static",
            "temporal": False,
            "unit": "binary",
            "legend_type": "categorical",
            "domain": [0, 1]
        }
    ]
}

output_path = Path("thesis_data/web_exports/metadata.json")
output_path.parent.mkdir(parents=True, exist_ok=True)

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(metadata, f, indent=2)

print(f"Saved metadata to {output_path}")
print(f"Number of layers: {len(metadata['layers'])}")
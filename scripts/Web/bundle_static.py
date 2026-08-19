import pandas as pd
from pathlib import Path
import json

df = pd.read_parquet("thesis_data/FINAL_DATA/static_data.parquet")

records = df.to_dict(orient="records")

output_path = Path("thesis_data/web_exports/static_data.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(records, f)

print(f"Saved {output_path}")
print(f"Rows: {len(records)}")
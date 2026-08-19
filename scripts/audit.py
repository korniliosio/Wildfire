import pandas as pd
import sys

def print_parquet_info(filepath):
  """Print detailed information about a parquet file."""
  try:
    df = pd.read_parquet(filepath)
    
    print(f"File: {filepath}\n")
    print(f"Shape: {df.shape[0]} rows × {df.shape[1]} columns\n")
    
    print("Columns and Data Types:")
    print(df.dtypes)
    
    print(f"\nMemory Usage:")
    print(df.memory_usage(deep=True))
    
    print(f"\nFirst few rows:")
    print(df.head())
    
    print(f"\nBasic Statistics:")
    print(df.describe())
    
  except FileNotFoundError:
    print(f"Error: File not found at {filepath}")
  except Exception as e:
    print(f"Error reading parquet file: {e}")

if __name__ == "__main__":
  if len(sys.argv) > 1:
    parquet_file = sys.argv[1]
  else:
    parquet_file = input("Enter parquet file path: ")
  
  print_parquet_info(parquet_file)
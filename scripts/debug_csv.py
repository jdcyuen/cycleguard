# scripts/debug_csv.py
# 👉 Converts any delimited file (Tab or Comma) into a clean Comma-Delimited CSV

import sys
import os
import pandas as pd

def convert_to_csv(file_path):
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return

    try:
        # 1. Read the file to find the header
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        with open(file_path, "r", encoding="latin-1") as f:
            lines = f.readlines()

    # 2. Find the 'Symbol' and 'Current Value' header index (Robust Detection)
    header_index = -1
    for i, line in enumerate(lines):
        norm_line = line.lower()
        if "symbol" in norm_line and "current value" in norm_line:
            header_index = i
            break

    if header_index == -1:
        print("❌ Error: Could not find 'Symbol' and 'Current Value' headers.")
        return

    # 3. Read with auto-separator detection (sep=None)
    try:
        df = pd.read_csv(
            file_path, 
            skiprows=header_index, 
            sep=None, 
            engine='python',
            on_bad_lines='skip'
        )
        
        # Normalize column names
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
        
        # Clean current_value (remove $, commas, and non-numeric characters)
        if "current_value" in df.columns and df["current_value"].dtype == 'object':
            df["current_value"] = (
                df["current_value"]
                .astype(str)
                .str.replace("$", "", regex=False)
                .str.replace(",", "", regex=False)
                .str.extract(r"(\d+\.?\d*)")
                .astype(float)
            )

        # 4. Output as clean Comma-Delimited CSV to stdout
        print(df.to_csv(index=False))
        
    except Exception as e:
        print(f"❌ Failed to process file: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/debug_csv.py <path_to_fidelity_file>")
    else:
        convert_to_csv(sys.argv[1])

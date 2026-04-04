# scripts/sync_portfolio.py
#
import pandas as pd
import json
from pathlib import Path

# Fix path to point to src/data/
PORTFOLIO_FILE = Path(__file__).resolve().parents[1] / "src" / "data" / "portfolio_state.json"


def load_fidelity_csv(file_path):
    try:
        # Fidelity CSVs often have metadata at the top.
        # We need to find the header row containing 'Symbol' and 'Current Value'.
        with open(file_path, "r") as f:
            lines = f.readlines()
        
        header_index = -1
        for i, line in enumerate(lines):
            if "symbol" in line.lower() and "current value" in line.lower():
                header_index = i
                break
        
        if header_index == -1:
            raise ValueError("No valid 'Symbol' and 'Current Value' headers found in CSV.")
            
        df = pd.read_csv(
            file_path, 
            skiprows=header_index,
            sep=None,
            on_bad_lines='skip',
            engine='python'
        )

        # Normalize column names
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

        if "symbol" not in df.columns or "current_value" not in df.columns:
            raise ValueError("CSV must contain 'Symbol' and 'Current Value' columns")

        # Clean symbols
        df["symbol"] = df["symbol"].astype(str).str.strip()
        
        # Clean current_value (remove $, commas, and non-numeric characters)
        if df["current_value"].dtype == 'object':
            df["current_value"] = (
                df["current_value"]
                .astype(str)
                .str.replace("$", "", regex=False)
                .str.replace(",", "", regex=False)
                .str.extract(r"(\d+\.?\d*)")
                .astype(float)
            )

        # Filter and group
        df = df.dropna(subset=["symbol", "current_value"])
        portfolio = df.groupby("symbol")["current_value"].sum().to_dict()
        
        return portfolio
        
    except Exception as e:
        print(f"❌ Failed to parse CSV: {e}")
        return None


def save_portfolio(portfolio):
    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(portfolio, f, indent=2)


def main():
    import os
    file_path = input("Enter path to Fidelity CSV: ").strip()
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return

    portfolio = load_fidelity_csv(file_path)
    if not portfolio:
        return

    print("\nPreview of imported portfolio:")
    for k, v in list(portfolio.items())[:5]:
        print(f"{k}: ${v:,.2f}")

    confirm = input("\nOverwrite portfolio_state.json? (y/n): ").lower()

    if confirm == "y":
        save_portfolio(portfolio)
        print("✅ Portfolio synced with Fidelity")
    else:
        print("❌ Sync cancelled")


if __name__ == "__main__":
    main()

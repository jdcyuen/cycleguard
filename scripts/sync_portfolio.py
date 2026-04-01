# scripts/sync_portfolio.py
#
import pandas as pd
import json
from pathlib import Path

PORTFOLIO_FILE = Path("data/portfolio_state.json")  # adjust path if needed


def load_fidelity_csv(file_path):
    df = pd.read_csv(file_path)

    # Normalize column names
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    # Expecting: symbol, current_value
    if "symbol" not in df.columns or "current_value" not in df.columns:
        raise ValueError("CSV must contain 'Symbol' and 'Current Value' columns")

    portfolio = dict(zip(df["symbol"], df["current_value"]))
    return portfolio


def save_portfolio(portfolio):
    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(portfolio, f, indent=2)


def main():
    file_path = input("Enter path to Fidelity CSV: ").strip()
    portfolio = load_fidelity_csv(file_path)

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

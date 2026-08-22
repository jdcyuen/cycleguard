import argparse
import pandas as pd
import yfinance as yf

'''
USAGE:
    python technical_indicators.py SPMO
    python technical_indicators.py FTEC --period 6mo
    python technical_indicators.py NVDA --period 3mo --interval 1h
'''




def parse_args():
    parser = argparse.ArgumentParser(
        description="Calculate technical indicators for a security."
    )

    parser.add_argument(
        "symbol",
        type=str,
        help="Ticker symbol (e.g. SPMO, FTEC, NVDA)"
    )

    parser.add_argument(
        "--period",
        default="2y",
        help="Price history period (default: 2y)"
    )

    parser.add_argument(
        "--interval",
        default="1d",
        help="Price interval (default: 1d)"
    )

    return parser.parse_args()


def main():

    args = parse_args()

    symbol = args.symbol.upper()

    df = yf.download(
        symbol,
        period="2y",
        interval="1d",
        auto_adjust=True,
        group_by="column",
        progress=True
    )

    # Handle MultiIndex columns (older/newer yfinance versions)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    close = df["Close"]

    df["EMA_8"] = close.ewm(span=8, adjust=False).mean()
    df["EMA_21"] = close.ewm(span=21, adjust=False).mean()
    df["EMA_50"] = close.ewm(span=50, adjust=False).mean()
    df["MA_200"] = close.rolling(200).mean()

    df["Pct_vs_8EMA"] = (close - df["EMA_8"]) / df["EMA_8"] * 100
    df["Pct_vs_21EMA"] = (close - df["EMA_21"]) / df["EMA_21"] * 100
    df["Pct_vs_50EMA"] = (close - df["EMA_50"]) / df["EMA_50"] * 100
    df["Pct_vs_200MA"] = (close - df["MA_200"]) / df["MA_200"] * 100

    delta = close.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()

    rs = avg_gain / avg_loss

    df["RSI_14"] = 100 - (100 / (1 + rs))

    df["Volume_20D_Avg"] = 
    
    
    df["Volume_Ratio"] = df["Volume"] / df["Volume_20D_Avg"]

    latest = df.iloc[-1]

    print(f"\nTechnical Snapshot for {symbol}")
    print("-" * 60)
    print(latest[
        [
            "Close",
            "EMA_8",
            "EMA_21",
            "EMA_50",
            "MA_200",
            "Pct_vs_8EMA",
            "Pct_vs_21EMA",
            "Pct_vs_50EMA",
            "Pct_vs_200MA",
            "RSI_14",
            "Volume_Ratio",
        ]
    ])


if __name__ == "__main__":
    main()
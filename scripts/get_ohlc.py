import argparse
import yfinance as yf

#OHLC -  Open, High, Low, and Close


def get_ohlc(symbol: str, days: int = 20):
    """Fetch recent daily OHLC data for a symbol."""
    ticker = yf.Ticker(symbol)

    df = ticker.history(
        period=f"{days + 5}d",
        interval="1d",
        auto_adjust=False,
    )

    if df.empty:
        raise RuntimeError(f"No data returned for {symbol}")

    # Keep only the requested number of trading days
    df = df.tail(days)

    # Keep only OHLC columns
    df = df[["Open", "High", "Low", "Close"]]

    # Make the date easier to read
    df.index = df.index.strftime("%Y-%m-%d")

    return df


def main():
    parser = argparse.ArgumentParser(
        description="Get recent daily OHLC data from Yahoo Finance."
    )

    parser.add_argument(
        "symbol",
        help="Ticker symbol, e.g. ICVT"
    )

    parser.add_argument(
        "--days",
        type=int,
        default=20,
        help="Number of trading days to return (default: 20)"
    )

    args = parser.parse_args()

    try:
        df = get_ohlc(args.symbol.upper(), args.days)

        print()
        print(f"{args.symbol.upper()} - Last {args.days} Trading Days")
        print("=" * 60)
        print(df.to_string())
        print()

    except Exception as exc:
        print(f"ERROR: {exc}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
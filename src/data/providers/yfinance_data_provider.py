import yfinance as yf
import pandas as pd

from data.providers.idata_provider import IDataProvider
from data.providers.data_provider_error import DataProviderError


class YFinanceDataProvider(IDataProvider):
    """Responsible ONLY for fetching data from yfinance."""

    def fetch_data(self, ticker: str, start_date: str) -> pd.DataFrame:

        try:
            df = yf.download(
                ticker,
                start=start_date,
                progress=False,
                auto_adjust=False,
            )
        except Exception as exc:
            raise DataProviderError(f"Failed to fetch market data for ticker: {ticker}") from exc

        if df.empty:
            raise DataProviderError(f"No data found for ticker {ticker}")

        df = df[["Close"]].dropna()
        df.columns = ["close"]
        return df

    def fetch_multiple_tickers(self, tickers: list[str], period: str = "1y") -> pd.DataFrame:
        if not tickers:
            return pd.DataFrame()

        try:
            df = yf.download(
                tickers,
                period=period,
                progress=False,
                auto_adjust=False,
        )
        except Exception as exc:
            raise DataProviderError(f"Failed to fetch market data for tickers: {tickers}") from exc

        if df.empty:
            return pd.DataFrame()

        if isinstance(df.columns, pd.MultiIndex):
            return df["Close"]

        # Single ticker case
        result = pd.DataFrame(df["Close"])
        result.columns = [tickers[0]]
        return result
# crash_manager.py

import pandas as pd
from config.config_manager import get_config
from data.providers.idata_provider import IDataProvider
from data.providers.yfinance_data_provider import YFinanceDataProvider


# CrashManager is the crash detection/calculation component.
# It takes market price data and determines the current drawdown from the cycle peak.

# -------------------------
# ENGINE (SRP / OCP / DIP)
# -------------------------
class CrashManager:
    """Responsible ONLY for calculating drawdown and crash signals."""

    def __init__(self, config=None, data_provider: IDataProvider = None):
        self.config = config if config else get_config()
        self.ticker = self.config["system"]["market"]["benchmark_ticker"]
        self.recovery_threshold = self.config["system"]["market"]["recovery_threshold"]

        # Dependency Injection (DIP)
        self.data_provider = data_provider if data_provider else YFinanceDataProvider()

    def detect_cycle_peak(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df

        peak = df["close"].iloc[0]
        peaks = []

        for price in df["close"]:
            # New high → reset peak
            if price > peak:
                peak = price
            # Recovery threshold → allow new peak
            elif price >= self.recovery_threshold * peak:
                peak = price
            peaks.append(peak)

        df["cycle_peak"] = peaks
        return df

    def calculate_drawdown(self, df: pd.DataFrame) -> pd.DataFrame:
        if not df.empty:
            df["drawdown"] = (df["close"] - df["cycle_peak"]) / df["cycle_peak"]
        return df

    def run(self):  
        """Run crash detection and return the current market drawdown."""
        df = self.data_provider.fetch_data(
            self.ticker, self.config["system"]["market"]["start_date"]
        )

        df = self.detect_cycle_peak(df)
        df = self.calculate_drawdown(df)

        if df.empty:
            return {
                "close": 0,
                "cycle_peak": 0,
                "drawdown": 0,
            }

        latest = df.iloc[-1]

        return {
            "close": latest["close"],
            "cycle_peak": latest["cycle_peak"],
            "drawdown": latest["drawdown"],
        }

# crash_manager.py

import yfinance as yf
import pandas as pd
from abc import ABC, abstractmethod
from src.config.config_loader import load_config


# -------------------------
# INTERFACE (DIP)
# -------------------------
class IMarketDataProvider(ABC):
    """Abstract interface for market data sources."""
    @abstractmethod
    def fetch_data(self, ticker: str, start_date: str) -> pd.DataFrame:
        pass


# -------------------------
# IMPLEMENTATION (SRP)
# -------------------------
class YFinanceDataProvider(IMarketDataProvider):
    """Responsible ONLY for fetching data from yfinance."""
    def fetch_data(self, ticker: str, start_date: str) -> pd.DataFrame:
        df = yf.download(ticker, start=start_date, progress=False)
        
        if df.empty:
            return pd.DataFrame(columns=["close"])
            
        df = df[["Close"]].dropna()
        df.columns = ["close"]
        return df


# -------------------------
# ENGINE (SRP / OCP / DIP)
# -------------------------
class CrashManager:
    """Responsible ONLY for calculating drawdown and crash signals."""
    def __init__(self, config=None, data_provider: IMarketDataProvider = None):
        self.config = config if config else load_config()
        self.ticker = self.config["market"]["ticker"]
        self.recovery_threshold = self.config["market"]["recovery_threshold"]
        self.levels = self.config["deployment"]["levels"]
        
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

    def get_signal(self, drawdown: float) -> str:
        # Sort levels by severity (largest drop first)
        sorted_levels = sorted(self.levels.items(), key=lambda x: x[1], reverse=True)

        for level_name, deploy_pct in sorted_levels:
            if level_name == "Level 4" and drawdown <= -0.40:
                return "Level 4"
            elif level_name == "Level 3" and drawdown <= -0.30:
                return "Level 3"
            elif level_name == "Level 2" and drawdown <= -0.20:
                return "Level 2"
            elif level_name == "Level 1" and drawdown <= -0.10:
                return "Level 1"

        return None

    def run(self):
        """Orchestrates the pipeline using the injected data provider."""
        # DIP: Calling the injected provider instead of yfinance directly
        df = self.data_provider.fetch_data(
            self.ticker, 
            self.config["market"]["start_date"]
        )
        
        df = self.detect_cycle_peak(df)
        df = self.calculate_drawdown(df)

        if df.empty:
            return {
                "price": 0,
                "cycle_peak": 0,
                "drawdown": 0,
                "signal": None,
            }

        latest = df.iloc[-1]
        signal = self.get_signal(latest["drawdown"])

        return {
            "price": latest["close"],
            "cycle_peak": latest["cycle_peak"],
            "drawdown": latest["drawdown"],
            "signal": signal,
        }

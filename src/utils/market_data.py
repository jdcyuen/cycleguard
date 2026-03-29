# market_data.py

import yfinance as yf
import pandas as pd
from src.config.config_loader import load_config


class MarketData:
    def __init__(self, config=None):
        self.config = config if config else load_config()
        self.ticker = self.config["market"]["ticker"]
        self.start_date = self.config["market"]["start_date"]
        self.recovery_threshold = self.config["market"]["recovery_threshold"]

    # =========================
    # FETCH MARKET DATA
    # =========================
    def fetch(self) -> pd.DataFrame:
        df = yf.download(self.ticker, start=self.start_date, progress=False)
        df = df[["Close"]].dropna()
        df.columns = ["close"]
        return df

    # =========================
    # CALCULATE CYCLE PEAK
    # =========================
    def detect_cycle_peak(self, df: pd.DataFrame) -> pd.DataFrame:
        peak = df["close"].iloc[0]
        peaks = []

        for price in df["close"]:
            # New high → update peak
            if price > peak:
                peak = price

            # Allow reset if near recovery
            elif price >= self.recovery_threshold * peak:
                peak = price

            peaks.append(peak)

        df["cycle_peak"] = peaks
        return df

    # =========================
    # CALCULATE DRAWDOWN
    # =========================
    def calculate_drawdown(self, df: pd.DataFrame) -> pd.DataFrame:
        df["drawdown"] = (df["close"] - df["cycle_peak"]) / df["cycle_peak"]
        return df

    # =========================
    # GET LATEST MARKET SNAPSHOT
    # =========================
    def latest(self) -> dict:
        df = self.fetch()
        df = self.detect_cycle_peak(df)
        df = self.calculate_drawdown(df)

        latest = df.iloc[-1]

        return {
            "price": latest["close"],
            "cycle_peak": latest["cycle_peak"],
            "drawdown": latest["drawdown"],
        }

    # =========================
    # FULL DATA PIPELINE
    # =========================
    def run(self) -> pd.DataFrame:
        df = self.fetch()
        df = self.detect_cycle_peak(df)
        df = self.calculate_drawdown(df)
        return df

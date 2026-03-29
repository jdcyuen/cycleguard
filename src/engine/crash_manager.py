# crash_manager.py

import yfinance as yf
import pandas as pd
from src.config.config_loader import load_config


class CrashManager:
    def __init__(self, config=None):
        self.config = config if config else load_config()
        self.ticker = self.config["market"]["ticker"]
        self.recovery_threshold = self.config["market"]["recovery_threshold"]
        self.levels = self.config["deployment"]["levels"]

    # =========================
    # FETCH MARKET DATA
    # =========================
    def fetch_data(self):
        df = yf.download(
            self.ticker, start=self.config["market"]["start_date"], progress=False
        )
        df = df[["Close"]].dropna()
        df.columns = ["close"]
        return df

    # =========================
    # DETECT CYCLE PEAK
    # =========================
    def detect_cycle_peak(self, df: pd.DataFrame) -> pd.DataFrame:
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

    # =========================
    # CALCULATE DRAWDOWN
    # =========================
    def calculate_drawdown(self, df: pd.DataFrame) -> pd.DataFrame:
        df["drawdown"] = (df["close"] - df["cycle_peak"]) / df["cycle_peak"]
        return df

    # =========================
    # GENERATE SIGNAL
    # =========================
    def get_signal(self, drawdown: float) -> str:
        # Sort levels by severity (largest drop first)
        sorted_levels = sorted(self.levels.items(), key=lambda x: x[1], reverse=True)

        for level_name, deploy_pct in sorted_levels:
            # Map level names to thresholds
            if level_name == "Level 4" and drawdown <= -0.40:
                return "Level 4"
            elif level_name == "Level 3" and drawdown <= -0.30:
                return "Level 3"
            elif level_name == "Level 2" and drawdown <= -0.20:
                return "Level 2"
            elif level_name == "Level 1" and drawdown <= -0.10:
                return "Level 1"

        return None

    # =========================
    # FULL PIPELINE
    # =========================
    def run(self):
        df = self.fetch_data()
        df = self.detect_cycle_peak(df)
        df = self.calculate_drawdown(df)

        latest = df.iloc[-1]

        signal = self.get_signal(latest["drawdown"])

        return {
            "price": latest["close"],
            "cycle_peak": latest["cycle_peak"],
            "drawdown": latest["drawdown"],
            "signal": signal,
        }

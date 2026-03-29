# cycleguard_dashboard.py

import streamlit as st
import pandas as pd
import json
from datetime import datetime
from src.config.config_loader import load_config
from src.utils.market_data import MarketData
from src.engine.crash_manager import CrashManager
from src.engine.recovery_manager import RecoveryManager
from src.engine.trades import TradeEngine

# =========================
# Load Config
# =========================
config = load_config()
PORTFOLIO_FILE = config["system"]["files"]["portfolio"]
STATE_FILE = config["system"]["files"]["rebalance"]
RECOVERY_FILE = config["system"]["files"]["recovery"]
TRADE_LOG = config["system"]["files"]["trades"]


# =========================
# Helpers
# =========================
@st.cache_data
def load_portfolio():
    try:
        with open(PORTFOLIO_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


@st.cache_data
def load_trade_log():
    try:
        df = pd.read_csv(TRADE_LOG)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df
    except FileNotFoundError:
        return pd.DataFrame(
            columns=["timestamp", "action", "ticker", "shares", "price"]
        )


@st.cache_data
def load_market_data():
    market = MarketData()
    df = market.run()
    return df


# =========================
# Dashboard Layout
# =========================
st.set_page_config(page_title="CycleGuard Dashboard", layout="wide")
st.title("🚀 CycleGuard Portfolio Dashboard")

# Portfolio Overview
portfolio = load_portfolio()
st.subheader("📊 Portfolio Overview")
portfolio_df = pd.DataFrame(list(portfolio.items()), columns=["Ticker", "Value ($)"])
portfolio_df["% of Portfolio"] = (
    portfolio_df["Value ($)"] / portfolio_df["Value ($)"].sum()
)
st.dataframe(
    portfolio_df.style.format({"Value ($)": "${:,.2f}", "% of Portfolio": "{:.2%}"})
)

st.write(f"**Total Portfolio Value:** ${portfolio_df['Value ($)'].sum():,.2f}")

# Market Data / Drawdowns
st.subheader("📈 Market Data & Drawdowns")
market_df = load_market_data()
latest_market = market_df.iloc[-1]
st.write(f"**Latest Market Price:** {latest_market['close']:.2f}")
st.write(f"**Cycle Peak:** {latest_market['cycle_peak']:.2f}")
st.write(f"**Current Drawdown:** {latest_market['drawdown']:.2%}")

st.line_chart(market_df[["close", "cycle_peak"]])
st.area_chart(market_df["drawdown"])

# Crash Signals
st.subheader("⚠️ Crash / Recovery Signals")
market_snapshot = {"drawdown": latest_market["drawdown"]}
crash_manager = CrashManager()
recovery_manager = RecoveryManager()
trades_engine = TradeEngine()

signal = crash_manager.get_signal(market_snapshot["drawdown"])
st.write(f"**Crash Signal:** {signal if signal else 'No crash signal'}")

# Trade Log
st.subheader("📋 Executed Trades")
trade_log_df = load_trade_log()
st.dataframe(trade_log_df.sort_values("timestamp", ascending=False))

# Recovery Recommendations
st.subheader("🛠️ Recovery Management")
portfolio_after_recovery = recovery_manager.trim_and_rebalance(
    portfolio, market_snapshot
)
st.dataframe(
    pd.DataFrame(
        list(portfolio_after_recovery.items()), columns=["Ticker", "Adjusted Value ($)"]
    )
)

# Footer
st.write(f"Dashboard last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

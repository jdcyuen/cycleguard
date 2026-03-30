# cycleguard_dashboard.py

import sys
import os

# Add project root to sys.path
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if root_path not in sys.path:
    sys.path.insert(0, root_path)

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
        df["date"] = pd.to_datetime(df["date"])
        return df
    except FileNotFoundError:
        return pd.DataFrame(columns=["date", "type", "asset", "amount", "reason"])


@st.cache_data
def load_rebalance_state():
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"last_run_date": None, "executed_levels": []}


@st.cache_data
def load_recovery_state():
    try:
        with open(RECOVERY_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"bottom": None, "recovered": False}


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


# =========================
# WHAT SHOULD I DO PANEL
# =========================
st.subheader("🧠 What Should I Do Today?")

total_value = sum(portfolio.values())
signal = crash_manager.get_signal(latest_market["drawdown"])

action_text = ""
details = []

# -------------------------
# CRASH ACTIONS
# -------------------------
if signal:
    deploy_pct = config["deployment"]["levels"][signal]
    deploy_amount = total_value * deploy_pct

    action_text = f"⚠️ {signal} Triggered"

    # Funding sources
    funding = config["funding"]["priority"]

    details.append(f"Deploy approximately **${deploy_amount:,.0f}** into equities")
    details.append(f"Sell from: {', '.join(funding[:2])}")

    # Buy targets
    buy_targets = config["buy_targets"][signal]
    top_targets = list(buy_targets.keys())[:3]
    details.append(f"Buy priority: {', '.join(top_targets)}")

# -------------------------
# RECOVERY ACTIONS
# -------------------------
else:
    recovery_state = load_recovery_state()

    # Simple recovery check
    rebound_threshold = config["recovery"]["rebound_threshold"]
    bottom = recovery_state.get("bottom")

    if bottom:
        rebound = (latest_market["close"] - bottom) / bottom

        if rebound >= rebound_threshold:
            action_text = "📈 Recovery Phase"

            trim_targets = config["recovery"]["trim_targets"]
            for asset, pct in trim_targets.items():
                details.append(f"Trim {asset} by {int(pct * 100)}%")

            details.append(f"Move proceeds to {config['recovery']['rebuild_cash_to']}")
        else:
            action_text = "🟢 No Action Needed"

    else:
        action_text = "🟢 No Action Needed"

# -------------------------
# DISPLAY
# -------------------------
st.markdown(f"### {action_text}")

for d in details:
    st.write(f"• {d}")


# =========================
# MISSED CRASH LEVELS
# =========================
st.subheader("⚡ Missed Crash Levels")

state = load_rebalance_state()

executed_levels = state.get("executed_levels", [])

if executed_levels:
    st.warning(
        "The following crash levels were triggered and executed (including catch-up from missed days):"
    )
    for level in executed_levels:
        st.write(f"• {level}")
else:
    st.success("No crash levels have been triggered yet.")


# Trade Log
st.subheader("📋 Executed Trades")
trade_log_df = load_trade_log()
st.dataframe(trade_log_df.sort_values("date", ascending=False))

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

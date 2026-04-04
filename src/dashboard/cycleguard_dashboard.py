# cycleguard_dashboard.py

import sys
import os
from pathlib import Path

# =========================
# SYSTEM PATHS & FIX
# =========================
# Add project root to sys.path so we can import src.*
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if root_path not in sys.path:
    sys.path.insert(0, root_path)

import streamlit as st
import json

from src.dashboard.components.sync_fidelity import render_sync_fidelity
from src.dashboard.components.action_panel import render_action_panel
from src.dashboard.components.trade_preview import render_trade_preview

from src.engine.crash_manager import CrashManager
from src.engine.recovery_manager import RecoveryManager
from src.data.market_data import get_market_data
from src.config.config_loader import load_config


# -------------------------
# FILE PATHS
# -------------------------
BASE_DIR = Path(__file__).resolve().parents[2]
# Note: Data files are actually in src/data/
PORTFOLIO_FILE = BASE_DIR / "src" / "data" / "portfolio_state.json"
STATE_FILE = BASE_DIR / "src" / "data" / "rebalance_state.json"
RECOVERY_FILE = BASE_DIR / "src" / "data" / "recovery_state.json"


# -------------------------
# LOADERS
# -------------------------
@st.cache_data
def load_portfolio():
    try:
        with open(PORTFOLIO_FILE, "r") as f:
            return json.load(f)
    except:
        return {}


@st.cache_data
def load_rebalance_state():
    # Merge rebalance and recovery states for the action panel
    combined_state = {"executed_levels": [], "bottom": None}

    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r") as f:
                rebalance = json.load(f)
                combined_state["executed_levels"] = rebalance.get("executed_levels", [])

        if os.path.exists(RECOVERY_FILE):
            with open(RECOVERY_FILE, "r") as f:
                recovery = json.load(f)
                combined_state["bottom"] = recovery.get("bottom")

    except Exception as e:
        st.error(f"Error loading states: {e}")

    return combined_state


# -------------------------
# INIT
# -------------------------
config = load_config()
portfolio = load_portfolio()

crash_manager = CrashManager(config)
recovery_manager = RecoveryManager(config)

latest_market = get_market_data()


# -------------------------
# UI START
# -------------------------
st.set_page_config(page_title="CycleGuard Dashboard", page_icon="📉", layout="wide")

# CSS to reduce top padding
st.markdown(
    """
    <style>
        .block-container {
            padding-top: 1.25rem;
            padding-bottom: 0rem;
            padding-left: 5rem;
            padding-right: 5rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("📉 CycleGuard Dashboard")


# =========================
# PORTFOLIO OVERVIEW
# =========================
with st.container(border=True):
    st.subheader("📊 Portfolio Overview")
    total_value = sum(portfolio.values())
    for ticker, value in portfolio.items():
        pct = (value / total_value) if total_value else 0
        st.write(f"{ticker}: ${value:,.2f} ({pct:.2%})")


# =========================
# SYNC WITH FIDELITY
# =========================
render_sync_fidelity(portfolio, PORTFOLIO_FILE)


# =========================
# MARKET DATA
# =========================
with st.container(border=True):
    st.subheader("📈 Market Data & Drawdown")
    st.write(f"Current Price: {latest_market['close']}")
    st.write(f"Cycle Peak: {latest_market['cycle_peak']}")
    st.write(f"Drawdown: {latest_market['drawdown']:.2%}")


# =========================
# CRASH SIGNALS
# =========================
with st.container(border=True):
    st.subheader("⚠️ Crash / Recovery Signals")
    signal = crash_manager.get_signal(latest_market["drawdown"])
    st.write(f"Current Signal: {signal if signal else 'None'}")


# =========================
# ACTION PANEL
# =========================
render_action_panel(
    portfolio,
    latest_market,
    crash_manager,
    recovery_manager,
    config,
    load_rebalance_state,
)


# =========================
# TRADE PREVIEW
# =========================
render_trade_preview(portfolio, latest_market, crash_manager, config)


# =========================
# MISSED CRASH LEVELS
# =========================
with st.container(border=True):
    st.subheader("⚡ Missed Crash Levels")
    state = load_rebalance_state()
    executed_levels = state.get("executed_levels", [])
    if executed_levels:
        for lvl in executed_levels:
            st.write(f"• {lvl}")
    else:
        st.write("No levels triggered yet.")


# =========================
# TRADE LOG
# =========================
with st.container(border=True):
    st.subheader("📋 Executed Trades")
    TRADE_LOG = BASE_DIR / "src" / "data" / "trade_log.csv"
    if TRADE_LOG.exists():
        import pandas as pd

        df = pd.read_csv(TRADE_LOG)
        st.dataframe(df)
    else:
        st.write("No trades executed yet.")


# =========================
# RECOVERY STATE
# =========================
with st.container(border=True):
    st.subheader("🛠️ Recovery State")
    st.write(state)

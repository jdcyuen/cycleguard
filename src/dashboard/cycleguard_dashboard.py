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
from src.dashboard.components.portfolio_view import render_portfolio_view

from src.engine.crash_manager import CrashManager
from src.engine.recovery_manager import RecoveryManager
from src.engine.market_phase_detector import MarketPhaseDetector
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
market_phase_detector = MarketPhaseDetector(config)

latest_market = get_market_data()
phase_data = market_phase_detector.run()

# -------------------------
# SIMULATION TOGGLE
# -------------------------
st.sidebar.title("🛠️ Developer Tools")
simulate_crash = st.sidebar.checkbox("🚨 Simulate Market Crash")
if simulate_crash:
    phase_data = {
        "trend": {"status": "Bearish", "value": 410.0, "dma200": 480.0, "dma50": 460.0},
        "breadth": {
            "status": "Weak",
            "value": 0.0,
            "passing": [],
            "failing": [
                "XLK",
                "XLF",
                "XLV",
                "XLY",
                "XLP",
                "XLE",
                "XLI",
                "XLB",
                "XLU",
                "XLRE",
                "XLC",
            ],
            "valid_total": 11,
        },
        "volatility": {"status": "Risk-off", "value": 45.2},
        "leadership": {
            "status": "Weak",
            "value": 0,
            "qqq": 375.0,
            "qqq_50": 402.0,
            "smh": 180.0,
            "smh_50": 195.0,
        },
        "credit": {
            "status": "Stressed",
            "value": 0.05,
            "jnk": 90.0,
            "shy": 85.0,
            "ratio_current": 1.058,
            "ratio_50": 1.074,
        },
        "regime": "DEFENSIVE",
        "score": 0,
    }

    # Also fake the crash manager signal
    latest_market["drawdown"] = -0.35


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
# MARKET PHASE INDICATOR
# =========================
with st.container(border=True):
    phase_colors = {"DEFENSIVE": "🔴", "TRANSITION": "🟡", "RISK_ON": "🟢"}
    phase = phase_data.get("regime", "UNKNOWN")
    icon = phase_colors.get(phase, "⚪")

    st.subheader(
        f"{icon} Market Phase: {phase} (Score: {phase_data.get('score', 0)}/10)"
    )

    phase_descriptions = {
        "RISK_ON": "Strong positive momentum across Trend and Breadth. Ideal environment for allocating capital to growth and risk assets.",
        "TRANSITION": "Mixed market signals. Elevated Volatility or failing Breadth suggests caution. Maintain current exposures but avoid heavy new risk allocations.",
        "DEFENSIVE": "Hostile, bearish conditions. Capital preservation is the absolute priority. Cash and defensive allocations should be protected until the Trend recovers.",
    }
    st.info(phase_descriptions.get(phase, "Evaluating market conditions..."))

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        trend = phase_data.get("trend", {})
        st.metric("📈 Trend (SPY)", trend.get("status", "Unknown"))
    with col2:
        breadth = phase_data.get("breadth", {})
        st.metric("📊 Breadth (Sectors)", breadth.get("status", "Unknown"))
    with col3:
        vol = phase_data.get("volatility", {})
        st.metric("🌪 Volatility (VIX)", vol.get("status", "Unknown"))
    with col4:
        leadership = phase_data.get("leadership", {})
        st.metric("🚀 Leadership", leadership.get("status", "Unknown"))
    with col5:
        credit = phase_data.get("credit", {})
        st.metric("💳 Credit Stress", credit.get("status", "Unknown"))

    with st.expander("🔍 Signal Logic & Raw Data"):
        breadth = phase_data.get("breadth", {})
        b_pass = len(breadth.get("passing", []))
        b_tot = breadth.get("valid_total", 11)
        b_fail = breadth.get("failing", [])

        if b_pass == b_tot:
            fail_str = " (All are healthy)"
        elif b_pass == 0:
            fail_str = " (All are crashing)"
        else:
            fail_str = f", {', '.join(b_fail)} are not"

        breadth_live = (
            f"{b_pass}/{b_tot} Select Sector SPDR ETFs are above their 50DMA{fail_str}"
        )
        leader = phase_data.get("leadership", {})
        credit = phase_data.get("credit", {})

        st.markdown(
            f"""
        ### 10-Point Grading System Breakdowns
        **1. 📈 Trend (SPY):** {"🟩 SPY > 50DMA and 200DMA (+2 pts)" if trend.get("status") == "Bullish" else ("🟨 SPY > 200DMA but < 50DMA (+1 pt)" if trend.get("status") == "Neutral" else "🟥 SPY < 200DMA (0 pts)")}.<br>
        Live Reading: SPY=\${trend.get("value", 0):.2f} | 50DMA=\${trend.get("dma50", 0):.2f} | 200DMA=\${trend.get("dma200", 0):.2f}
        
        **2. 📊 Breadth (Sectors):** {"🟩 > 60% of Sectors > 50DMA (+2 pts)" if breadth.get("status") == "Strong" else ("🟨 40-60% of Sectors > 50DMA (+1 pt)" if breadth.get("status") == "Improving" else "🟥 < 40% of Sectors > 50DMA (0 pts)")}.<br>
        Live Reading: {breadth_live}
        
        **3. 🌪 Volatility (VIX):** {"🟩 VIX < 18 (+2 pts)" if vol.get("status") == "Calm" else ("🟨 VIX 18-25 (+1 pt)" if vol.get("status") == "Neutral" else "🟥 VIX > 25 (0 pts)")}.<br>
        Live Reading: {vol.get("value", 0):.2f}
        
        **4. 🚀 Leadership (SMH & QQQ):** {"🟩 Both SMH & QQQ > 50DMA (+2 pts)" if leader.get("status") == "Strong" else ("🟨 One > 50DMA (+1 pt)" if leader.get("status") == "Mixed" else "🟥 Both < 50DMA (0 pts)")}.<br>
        Live Reading: QQQ=\${leader.get("qqq", 0):.2f} (50DMA=\${leader.get("qqq_50", 0):.2f}) | SMH=\${leader.get("smh", 0):.2f} (50DMA=\${leader.get("smh_50", 0):.2f})
        
        **5. 💳 Credit Stress (JNK/SHY):** {"🟩 Ratio > 50DMA (+2 pts)" if credit.get("status") == "Healthy" else "🟥 Ratio < 50DMA (0 pts)"}.<br>
        Live Reading: JNK=\${credit.get("jnk", 0):.2f} | SHY=\${credit.get("shy", 0):.2f} | Current Ratio={credit.get("ratio_current", 0):.3f} (50DMA={credit.get("ratio_50", 0):.3f})

        
        ---
        **Total Current Score:** {phase_data.get("score", 0)} / 10
        *(RISK_ON: >= 7 | TRANSITION: 4-6 | DEFENSIVE: <= 3)*
        """,
            unsafe_allow_html=True,
        )

        # Keep the raw dictionary dump at the bottom for true developers
        st.json(phase_data)


# =========================
# PORTFOLIO OVERVIEW
# =========================
render_portfolio_view(portfolio)


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
    st.write(f"Current Signal: **{signal if signal else 'None'}**")

    if signal:
        descriptions = {
            "Level 1": "A Level 1 signal represents a mild market correction scenario where the broad market (S&P 500) has drawn down -10% from its cycle peak.",
            "Level 2": "A Level 2 signal represents a meaningful market pullback scenario where the broad market (S&P 500) has drawn down -20% from its cycle peak.",
            "Level 3": "A Level 3 signal represents a severe market crash scenario where the broad market (S&P 500) has drawn down -30% from its cycle peak.",
            "Level 4": "A Level 4 signal represents a catastrophic market collapse scenario where the broad market (S&P 500) has drawn down -40% from its cycle peak.",
        }
        st.info(descriptions.get(signal, "Deploying cash into the market discount."))


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
    phase_data,
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

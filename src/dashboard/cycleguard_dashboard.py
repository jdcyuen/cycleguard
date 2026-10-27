# cycleguard_dashboard.py

import sys
import os
from decimal import Decimal
from pathlib import Path

from engine.regime.regime_engine import RegimeEngine

# =========================
# SYSTEM PATHS & FIX
# =========================
# Add project root to sys.path so we can import src.*
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if root_path not in sys.path:
    sys.path.insert(0, root_path)

from src.core.logger import setup_logging

setup_logging()

import streamlit as st

st.set_page_config(page_title="CycleGuard Dashboard", page_icon="ðŸ“‰", layout="wide")

import json

from src.dashboard.components.sync_fidelity import render_sync_fidelity
from src.dashboard.components.action_panel import render_action_panel
from src.dashboard.components.trade_preview import render_trade_preview
from src.dashboard.components.portfolio_view import render_portfolio_view
from src.dashboard.components.drift_detection import render_drift_detection

from src.engine.crash_manager import CrashManager
from src.engine.recovery_manager import RecoveryManager
from src.engine.market_phase_detector import MarketPhaseDetector
from src.data.market_data import get_market_data

from src.config.config_manager import get_config

import logging

from repositories.account_repo import AccountRepository
from repositories.snapshot_repo import SnapshotRepository
from repositories.position_repo import PositionRepository

from services.portfolio_aggregation_service import (
    PortfolioAggregationService,
)
from services.deployment_orchestration_service import (
    DeploymentOrchestrationService,
)
from engine.deployment.cash_deployment_policy import CashDeploymentPolicy
from engine.deployment.regime_deployment_engine import (
    RegimeDeploymentEngine,
)
from engine.deployment.crash_deployment_engine import (
    CrashDeploymentEngine,
)
from engine.allocation.allocation_engine import AllocationEngine
from engine.allocation.current_weight_proportional_strategy import (
    CurrentWeightProportionalStrategy,
)
from database.connection import DBConnection
from config.account_config_loader import AccountConfigLoader


logger = logging.getLogger(__name__)


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

@st.cache_resource
def get_deployment_db_connection():
    db_connection = DBConnection()
    connection = db_connection.connect()
    return db_connection, connection
	
# -------------------------
# INIT
# -------------------------
config = get_config()
portfolio = load_portfolio()

crash_manager = CrashManager(config)
recovery_manager = RecoveryManager(config)

market_phase_detector = MarketPhaseDetector(config)
regime_config = config["regime"]["regime_system"]
regime_engine = RegimeEngine(regime_config)

latest_market = get_market_data()
market_regime_data = market_phase_detector.get_regime_data()
regime_result = regime_engine.evaluate(market_regime_data)

# -------------------------
# DEPLOYMENT ORCHESTRATION
# -------------------------
db_connection, db_conn = get_deployment_db_connection()

account = AccountConfigLoader().get("rollover_ira")
if account is None:
    st.error(
        "Deployment recommendations unavailable: "
        "account configuration 'rollover_ira' could not be loaded."
    )
    st.stop()

account_repository = AccountRepository(db_conn)
snapshot_repository = SnapshotRepository(db_conn)
position_repository = PositionRepository(db_conn)

portfolio_service = PortfolioAggregationService(
    position_repository,
    account,
)

deployment_config = regime_config.get("deployment", {})

crash_execution_rules = config.get(
    "crash_deployment", {}
).get("execution_rules", {})

cash_deployment_policy = CashDeploymentPolicy(
    max_deployment_per_event=Decimal(
        str(crash_execution_rules.get("max_deployment_per_event", 0.15))
    ),
)

deployment_policy = {
    regime: value
    for regime, value in deployment_config.items()
    if regime in {"RISK_ON", "TRANSITION", "DEFENSIVE", "CRISIS"}
}

regime_deployment_engine = RegimeDeploymentEngine(
    deployment_policy=deployment_policy,
)

crash_deployment_engine = CrashDeploymentEngine(
    config.get("crash_deployment", {}),
)

allocation_engine = AllocationEngine(
    CurrentWeightProportionalStrategy()
)

deployment_orchestration_service = DeploymentOrchestrationService(
    portfolio_service=portfolio_service,
    regime_engine=regime_engine,
    crash_manager=crash_manager,
    regime_deployment_engine=regime_deployment_engine,
    crash_deployment_engine=crash_deployment_engine,
    account=account,
    allocation_engine=allocation_engine,
    account_repository=account_repository,
    snapshot_repository=snapshot_repository,
    cash_deployment_policy=cash_deployment_policy,
)

phase_data = {
    **regime_result["signals"],
    "regime": regime_result["regime"],
}

# -------------------------
# SIMULATION TOGGLE
# -------------------------
st.sidebar.title("🛠️ Developer Tools")
simulate_crash = st.sidebar.checkbox("🚨 Simulate Market Crash")
if simulate_crash:
    phase_data = {
        "trend": {
            "status": "bearish",
            "proxy": "SPY",
            "value": 410.0,
            "dma50": 460.0,
            "dma200": 480.0,
        },
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
        "volatility": {
            "status": "risk-off",
            "value": 45.2,
        },
        "leadership": {
            "status": "Weak",
            "above_50": 0,
            "total": 2,
        },
        "credit": {
            "status": "Stressed",
        },
        "cape": {
            "status": "expensive",
            "value": 35.0,
        },
        "regime": "DEFENSIVE",
    }

    # Also fake the crash manager signal
    latest_market["drawdown"] = -0.35


# -------------------------
# UI START
# -------------------------

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
        f"{icon} Market Regime: {phase}"
    )

    phase_descriptions = {
        "RISK_ON": "Strong positive momentum across Trend and Breadth. Ideal environment for allocating capital to growth and risk assets.",
        "TRANSITION": "Mixed market signals. Elevated Volatility or failing Breadth suggests caution. Maintain current exposures but avoid heavy new risk allocations.",
        "DEFENSIVE": "Hostile, bearish conditions. Capital preservation is the absolute priority. Cash and defensive allocations should be protected until the Trend recovers.",
    }
    st.info(phase_descriptions.get(phase, "Evaluating market conditions..."))

    col1, col2, col3, col4, col5, col6 = st.columns(6)
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
    with col6:
        cape = phase_data.get("cape", {})
        st.metric("💰 Valuation (CAPE)", cape.get("status", "Unknown"))

    with st.expander("🔍 Signal Logic & Raw Data"):
        breadth = phase_data.get("breadth", {})
        b_pass = len(breadth.get("passing", []))
        b_tot = breadth.get("valid_total", 11)
        b_fail = breadth.get("failing", [])

        if b_pass == b_tot:
            fail_str = " (All are above their 50DMA)"
        elif b_pass == 0:
            fail_str = " (None are above their 50DMA)"
        else:
            fail_str = f" ({', '.join(b_fail)} are below their 50DMA)"

        breadth_live = (
            f"{b_pass}/{b_tot} sectors are above their 50DMA{fail_str}"
        )
        leader = phase_data.get("leadership", {})
        credit = phase_data.get("credit", {})

        st.markdown(
            f"""
        ### Regime Signal Details
       **1. 📈 Trend ({trend.get("evidence", {}).get("comparison", {}).get("proxy", "SPY")}):** {trend.get("evidence", {}).get("why", "No explanation available.")}.<br>
        Live Reading: SPY=${trend.get("value", 0):.2f} | 50DMA=${trend.get("dma50", 0):.2f} | 200DMA=${trend.get("dma200", 0):.2f}
        
        **2. 📊 Breadth (Sectors):** {breadth.get("evidence", {}).get("why", "No explanation available.")}<br>
        Live Reading: {breadth_live}
        
        **3. 🌪 Volatility (VIX):** {vol.get("evidence", {}).get("why", "No explanation available.")}<br>
        Live Reading: {vol.get("value", 0):.2f}
        
        **4. 🚀 Leadership (SMH & QQQ):** {leader.get("evidence", {}).get("why", "No explanation available.")}<br>
        Live Reading: {leader.get("above_50", 0)} of {leader.get("total", 0)} leadership proxies are above their 50DMA
        
        **5. 💳 Credit Stress (JNK/SHY):** {credit.get("evidence", {}).get("why", "No explanation available.")}<br>
        Live Reading: Current Ratio={credit.get("ratio_current", 0):.3f} (50DMA={credit.get("ratio_50", 0):.3f})

        **6. 💰 Valuation (CAPE):** {phase_data.get("cape", {}).get("evidence", {}).get("why", "No explanation available.")}<br>
        Live Reading: CAPE={cape.get("value", 0):.2f}
        
        ---
        *(Market regime is determined by the configured RegimeEngine conditions.)*
        """,
            unsafe_allow_html=True,
        )

        # Keep the raw dictionary dump at the bottom for true developers
        st.json(phase_data)


# PORTFOLIO OVERVIEW
render_portfolio_view(portfolio)


# =========================
# DRIFT DETECTION
# =========================
render_drift_detection(
    db_conn,
    account_repository,
    snapshot_repository,
)


# =========================
# SYNC WITH FIDELITY
# =========================
render_sync_fidelity(portfolio, PORTFOLIO_FILE)


# =========================
# MARKET DATA
# =========================
with st.container(border=True):
    st.subheader("📈 Market Data & Drawdown")
    st.write(f"S&P 500 Current Price: {latest_market['close']}")
    st.write(f"S&P 500 Cycle Peak: {latest_market['cycle_peak']}")
    st.write(f"S&P 500 Drawdown: {latest_market['drawdown']:.2%}")


# =========================
# CRASH SIGNALS
# =========================
with st.container(border=True):
    st.subheader("⚠️ Crash / Recovery Signals")
    crash_data = crash_manager.run()
    drawdown = crash_data.get("drawdown", 0)
    st.write(f"Current Drawdown: **{drawdown:.2%}**")

    # Drawdown = (Current Price - Cycle Peak) / Cycle Peak
    if drawdown <= -0.40:       # 40% from peak
        signal = "Level 4"
    elif drawdown <= -0.30:     # 30% from peak
        signal = "Level 3"
    elif drawdown <= -0.20:     # 20% from peak
        signal = "Level 2"
    elif drawdown <= -0.10:     # 10% from peak
        signal = "Level 1"
    else:
        signal = None

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
crash_decision = render_action_panel(
    portfolio,
    latest_market,
    crash_manager,
    recovery_manager,
    config,
    load_rebalance_state,
    phase_data,
    deployment_orchestration_service,
    market_regime_data,
)


# =========================
# TRADE PREVIEW
# =========================
render_trade_preview(portfolio, latest_market, crash_manager, config, phase_data)


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

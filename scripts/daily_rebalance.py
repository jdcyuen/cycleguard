# daily_rebalance.py (updated with missed-day recovery)

from src.config.config_loader import load_config
from src.utils.market_data import MarketData
from src.engine.crash_manager import CrashManager
from src.engine.recovery_manager import RecoveryManager
from src.engine.trades import TradeEngine
import json
from datetime import datetime, timedelta

# Load config & file paths
config = load_config()
PORTFOLIO_FILE = config["system"]["files"]["portfolio"]
STATE_FILE = config["system"]["files"]["rebalance"]
RECOVERY_FILE = config["system"]["files"]["recovery"]
TRADE_LOG = config["system"]["files"]["trades"]


# Load portfolio
def load_portfolio():
    try:
        with open(PORTFOLIO_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_portfolio(portfolio):
    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(portfolio, f, indent=2)


# Load rebalance state
def load_rebalance_state():
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"last_run_date": None, "executed_levels": []}


def save_rebalance_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


# Main daily rebalance function
def main():
    portfolio = load_portfolio()
    state = load_rebalance_state()
    market = MarketData()
    crash_manager = CrashManager()
    recovery_manager = RecoveryManager()
    trades_engine = TradeEngine()

    today = datetime.today().date()
    last_run_date = (
        datetime.fromisoformat(state["last_run_date"]).date()
        if state["last_run_date"]
        else today - timedelta(days=1)
    )

    # 1️⃣ Determine all missed days
    missed_days = [
        last_run_date + timedelta(days=i)
        for i in range(1, (today - last_run_date).days + 1)
    ]

    # 2️⃣ Check crash levels for each missed day
    for day in missed_days:
        market_snapshot = market.get_snapshot_for_date(day)
        if market_snapshot is None:
            continue  # Skip non-trading days

        drawdown = market_snapshot["drawdown"]
        crash_signal = crash_manager.get_signal(drawdown)

        if crash_signal and crash_signal not in state["executed_levels"]:
            result = trades_engine.execute_crash(crash_signal, portfolio)
            portfolio = result["portfolio"]
            state["executed_levels"].append(crash_signal)
            print(f"[{day}] Executed missed crash level {crash_signal}")
            print(f"  Sells: {result['sells']}")
            print(f"  Buys: {result['buys']}")

    # 3️⃣ Recovery logic
    latest_market_snapshot = market.latest()
    portfolio = recovery_manager.trim_and_rebalance(portfolio, latest_market_snapshot)

    # 4️⃣ Save state
    save_portfolio(portfolio)
    state["last_run_date"] = today.isoformat()
    save_rebalance_state(state)

    print(
        f"✅ Daily rebalance completed. Portfolio value: ${sum(portfolio.values()):,.2f}"
    )


# Entry point
if __name__ == "__main__":
    main()

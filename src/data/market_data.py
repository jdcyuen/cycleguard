# src/data/market_data.py
# 👉 Lightweight wrapper for the MarketData engine to return a clean dictionary

from src.engine.crash_manager import CrashManager
from src.config.config_loader import load_config

def get_market_data():
    config = load_config()
    manager = CrashManager(config)
    
    # Get latest snapshot from the crash manager engine
    snapshot = manager.run()
    
    # Return dictionary with predictable keys used by the dashboard:
    # 'close' (from dashboard) matches 'price' (from engine)
    # 'drawdown' is consistent
    return {
        "close": snapshot["price"],
        "drawdown": snapshot["drawdown"],
        "cycle_peak": snapshot["cycle_peak"]
    }

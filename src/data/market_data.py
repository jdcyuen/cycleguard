# src/data/market_data.py
# 👉 Lightweight wrapper for the MarketData engine to return a clean dictionary

from src.utils.market_data import MarketData
from src.config.config_loader import load_config

def get_market_data():
    config = load_config()
    market = MarketData(config)
    
    # Get latest snapshot
    snapshot = market.latest()
    
    # Return dictionary with predictable keys used by the dashboard:
    # 'close' (from dashboard) matches 'price' (from engine)
    # 'drawdown' is consistent
    return {
        "close": snapshot["price"],
        "drawdown": snapshot["drawdown"],
        "cycle_peak": snapshot["cycle_peak"]
    }

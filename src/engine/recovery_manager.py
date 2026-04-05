# recovery_manager.py

import json
import os
from abc import ABC, abstractmethod
from src.config.config_loader import load_config


# -------------------------
# INTERFACE (DIP)
# -------------------------
class IRecoveryStateStore(ABC):
    """Abstract interface for recovery state persistence."""
    @abstractmethod
    def load(self) -> dict:
        pass

    @abstractmethod
    def save(self, state: dict):
        pass


# -------------------------
# IMPLEMENTATION (SRP)
# -------------------------
class JSONRecoveryStateStore(IRecoveryStateStore):
    """Responsible ONLY for loading/saving state to a JSON file."""
    def __init__(self, state_file: str):
        self.state_file = state_file

    def load(self) -> dict:
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {"bottom": None, "recovered": False}
        return {"bottom": None, "recovered": False}

    def save(self, state: dict):
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        with open(self.state_file, "w") as f:
            json.dump(state, f, indent=4)


# -------------------------
# ENGINE (SRP / OCP / DIP)
# -------------------------
class RecoveryManager:
    """Responsible ONLY for recovery strategy logic and rebound detection."""
    def __init__(self, config=None, state_store: IRecoveryStateStore = None):
        self.config = config if config else load_config()
        recovery_config = self.config.get("recovery", {})
        
        self.rebound_threshold = recovery_config.get("rebound_threshold", 0.20)
        self.trim_targets = recovery_config.get("trim_targets", {})
        self.rebuild_cash_to = recovery_config.get("rebuild_cash_to", "SGOV")
        
        # Dependency Injection (DIP)
        if state_store:
            self.state_store = state_store
        else:
            # Default to JSON storage
            state_file = self.config.get("system", {}).get("files", {}).get("recovery", "src/data/recovery_state.json")
            self.state_store = JSONRecoveryStateStore(state_file)

    def load_state(self):
        return self.state_store.load()

    def save_state(self, state):
        self.state_store.save(state)

    def reset_state(self):
        self.save_state({"bottom": None, "recovered": False})

    def trim_and_rebalance(self, portfolio: dict, market_snapshot: dict) -> dict:
        """
        Calculates rebound from bottom and executes trims if threshold is met.
        """
        state = self.load_state()
        current_price = market_snapshot.get("price")
        
        if current_price is None:
            return portfolio
            
        # 1. Reset if we are at a new peak (drawdown is 0 or positive)
        if market_snapshot.get("drawdown", -1) >= 0:
            if state["bottom"] is not None or state["recovered"]:
                self.reset_state()
            return portfolio

        # 2. Update the "Market Bottom" if we set a new low
        bottom = state.get("bottom")
        if bottom is None or current_price < bottom:
            state["bottom"] = current_price
            state["recovered"] = False
            self.save_state(state)
            return portfolio
            
        # 3. Check for recovery rebound (Take Profit phase)
        if not state["recovered"]:
            rebound_target = bottom * (1.0 + self.rebound_threshold)
            
            if current_price >= rebound_target:
                # RECOVERY TRIGGERED! 
                total_cash_raised = 0.0
                
                for ticker, trim_pct in self.trim_targets.items():
                    if ticker in portfolio and portfolio[ticker] > 0:
                        trim_amount = portfolio[ticker] * trim_pct
                        portfolio[ticker] -= trim_amount
                        total_cash_raised += trim_amount
                
                # Rebuild cash position
                if total_cash_raised > 0:
                    cash_ticker = self.rebuild_cash_to
                    portfolio[cash_ticker] = portfolio.get(cash_ticker, 0.0) + total_cash_raised
                
                # Mark as recovered so we don't trigger again until next cycle
                state["recovered"] = True
                self.save_state(state)

        return portfolio

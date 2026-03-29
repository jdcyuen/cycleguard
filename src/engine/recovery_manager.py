import json
import os
from src.config.config_loader import load_config


class RecoveryManager:
    def __init__(self, config=None):
        self.config = config if config else load_config()
        recovery_config = self.config.get("recovery", {})
        
        self.rebound_threshold = recovery_config.get("rebound_threshold", 0.20)
        self.trim_targets = recovery_config.get("trim_targets", {})
        self.rebuild_cash_to = recovery_config.get("rebuild_cash_to", "SGOV")
        
        # We need the path to the recovery state file
        try:
            self.state_file = self.config["system"]["files"]["recovery"]
        except KeyError:
            self.state_file = "src/data/recovery_state.json"

    def load_state(self):
        if os.path.exists(self.state_file):
            with open(self.state_file, "r") as f:
                return json.load(f)
        return {"bottom": None, "recovered": False}

    def save_state(self, state):
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        with open(self.state_file, "w") as f:
            json.dump(state, f, indent=4)

    def reset_state(self):
        self.save_state({"bottom": None, "recovered": False})

    def trim_and_rebalance(self, portfolio: dict, market_snapshot: dict) -> dict:
        """
        Trims target positions and rotates into cash if the market rebounds past
        the defined threshold from the bottom.
        
        Args:
            portfolio: Dictionary of ticker -> dollar value holdings
            market_snapshot: Dictionary with at least 'price', 'cycle_peak', and 'drawdown'
            
        Returns:
            Updated portfolio dictionary.
        """
        state = self.load_state()
        current_price = market_snapshot.get("price")
        
        if current_price is None:
            return portfolio
            
        # Check if we are at a new cycle peak (drawdown is 0 or >= 0)
        if market_snapshot.get("drawdown", -1) >= 0:
            # We are recovered / back to peak, reset state
            if state["bottom"] is not None or state["recovered"]:
                self.reset_state()
            return portfolio

        # Update bottom if it's lower or not yet set
        bottom = state.get("bottom")
        if bottom is None or current_price < bottom:
            state["bottom"] = current_price
            state["recovered"] = False
            self.save_state(state)
            return portfolio
            
        # We have a valid bottom. Check for recovery rebound.
        if not state["recovered"]:
            rebound_target = bottom * (1.0 + self.rebound_threshold)
            
            if current_price >= rebound_target:
                # RECOVERY TRIGGERED! Execute trims.
                total_cash_raised = 0.0
                
                for ticker, trim_pct in self.trim_targets.items():
                    if ticker in portfolio and portfolio[ticker] > 0:
                        trim_amount = portfolio[ticker] * trim_pct
                        portfolio[ticker] -= trim_amount
                        total_cash_raised += trim_amount
                        print(f"Recovery Triggered! Trimmed {trim_pct*100}% of {ticker} (${trim_amount:,.2f})")
                
                # Rebuild cash position
                if total_cash_raised > 0:
                    cash_ticker = self.rebuild_cash_to
                    portfolio[cash_ticker] = portfolio.get(cash_ticker, 0.0) + total_cash_raised
                    print(f"Rotated ${total_cash_raised:,.2f} into {cash_ticker}")
                
                # Mark as recovered so we don't trigger again until next cycle
                state["recovered"] = True
                self.save_state(state)

        return portfolio

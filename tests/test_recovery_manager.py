import unittest
from unittest.mock import MagicMock
from src.engine.recovery_manager import RecoveryManager, IRecoveryStateStore


class TestRecoveryManager(unittest.TestCase):
    def setUp(self):
        # Mock Config
        self.mock_config = {
            "recovery": {
                "rebound_threshold": 0.20,
                "trim_targets": {"SMH": 0.5, "SCHG": 0.5},
                "rebuild_cash_to": "SGOV"
            },
            "system": {
                "files": {
                    "recovery": "test_recovery.json"
                }
            }
        }
        
        # Inject a mock state store to comply with DIP
        self.mock_store = MagicMock(spec=IRecoveryStateStore)
        self.rm = RecoveryManager(self.mock_config, state_store=self.mock_store)

    def test_update_bottom(self):
        """Verifies that the manager updates the bottom and saves state."""
        # Initial state (None)
        self.mock_store.load.return_value = {"bottom": None, "recovered": False}
        
        portfolio = {"SMH": 1000}
        market = {"price": 100.0, "drawdown": -0.1} # -10% from unknown peak
        
        # Run
        new_portfolio = self.rm.trim_and_rebalance(portfolio.copy(), market)
        
        # Verify
        self.mock_store.load.assert_called()
        self.mock_store.save.assert_called_with({"bottom": 100.0, "recovered": False})
        self.assertEqual(new_portfolio["SMH"], 1000) # No trim at bottom

    def test_recovery_trigger(self):
        """Verifies that recovery (trims) triggers at the rebound target."""
        # Setup: Bottom was at 80. Rebound threshold is 20%. Target is 96.
        self.mock_store.load.return_value = {"bottom": 80.0, "recovered": False}
        
        portfolio = {"SMH": 1000, "SGOV": 500}
        market = {"price": 97.0, "drawdown": -0.03} # Rebound hit!
        
        # Run
        new_portfolio = self.rm.trim_and_rebalance(portfolio.copy(), market)
        
        # Verify result
        # SMH should be trimmed by 50% ($500)
        self.assertEqual(new_portfolio["SMH"], 500)
        # SGOV should be increased by $500
        self.assertEqual(new_portfolio["SGOV"], 1000)
        
        # Verify state saved as recovered
        self.mock_store.save.assert_called_with({"bottom": 80.0, "recovered": True})

    def test_reset_at_peak(self):
        """Verifies that state is reset when market returns to peak."""
        # Setup: We were in a recovery state
        self.mock_store.load.return_value = {"bottom": 80.0, "recovered": True}
        
        portfolio = {"SMH": 1000}
        market = {"price": 120.0, "drawdown": 0.0} # BACK TO PEAK
        
        # Run
        self.rm.trim_and_rebalance(portfolio, market)
        
        # Verify store was asked to reset (saved with default empty state)
        self.mock_store.save.assert_called_with({"bottom": None, "recovered": False})


if __name__ == "__main__":
    unittest.main()

import unittest
import os
import tempfile
from src.engine.recovery_manager import RecoveryManager


class TestRecoveryManager(unittest.TestCase):
    def setUp(self):
        # Create a temporary file to act as the recovery state file
        self.test_dir = tempfile.TemporaryDirectory()
        self.state_file = os.path.join(self.test_dir.name, "test_recovery_state.json")

        # Mock Config
        self.mock_config = {
            "recovery": {
                "rebound_threshold": 0.20,
                "trim_targets": {"SMH": 0.20, "SCHG": 0.15},
                "rebuild_cash_to": "SGOV",
            },
            "system": {"files": {"recovery": self.state_file}},
        }

        self.rm = RecoveryManager(self.mock_config)
        self.portfolio = {
            "SMH": 10000.0,
            "SCHG": 20000.0,
            "SGOV": 5000.0,
            "AAPL": 15000.0,
        }

    def tearDown(self):
        self.test_dir.cleanup()

    def test_initial_state(self):
        state = self.rm.load_state()
        self.assertIsNone(state["bottom"])
        self.assertFalse(state["recovered"])

    def test_no_drawdown_resets_state(self):
        # Set a dummy state
        self.rm.save_state({"bottom": 80.0, "recovered": True})

        # Market is at new peak (drawdown 0)
        market_snapshot = {"price": 120.0, "drawdown": 0.0}
        portfolio_after = self.rm.trim_and_rebalance(
            self.portfolio.copy(), market_snapshot
        )

        # Portfolio should be unchanged
        self.assertEqual(portfolio_after["SMH"], 10000.0)

        # State should be reset
        state = self.rm.load_state()
        self.assertIsNone(state["bottom"])
        self.assertFalse(state["recovered"])

    def test_new_bottom_updates_state(self):
        # Initial drop
        market_snapshot = {"price": 90.0, "drawdown": -0.10}
        self.rm.trim_and_rebalance(self.portfolio, market_snapshot)

        state = self.rm.load_state()
        self.assertEqual(state["bottom"], 90.0)

        # Further drop
        market_snapshot = {"price": 80.0, "drawdown": -0.20}
        self.rm.trim_and_rebalance(self.portfolio, market_snapshot)

        state = self.rm.load_state()
        self.assertEqual(state["bottom"], 80.0)

    def test_recovery_trigger_and_trim(self):
        # 1. Establish a bottom
        market_snapshot = {"price": 100.0, "drawdown": -0.30}
        self.rm.trim_and_rebalance(self.portfolio, market_snapshot)

        # 2. Rebound slightly (not 20%) -> 110.0 is +10%
        market_snapshot = {"price": 110.0, "drawdown": -0.23}
        portfolio_after_10pct = self.rm.trim_and_rebalance(
            self.portfolio.copy(), market_snapshot
        )

        # Should be completely unchanged
        self.assertEqual(portfolio_after_10pct["SMH"], 10000.0)
        self.assertFalse(self.rm.load_state()["recovered"])

        # 3. Rebound 20% -> 120.0 is exactly +20%
        market_snapshot = {"price": 120.0, "drawdown": -0.16}
        portfolio_recovered = self.rm.trim_and_rebalance(
            self.portfolio.copy(), market_snapshot
        )

        # Should have trimmed 20% of SMH (10000 * 0.20 = 2000)
        self.assertEqual(portfolio_recovered["SMH"], 8000.0)

        # Should have trimmed 15% of SCHG (20000 * 0.15 = 3000)
        self.assertEqual(portfolio_recovered["SCHG"], 17000.0)

        # AAPL untouched
        self.assertEqual(portfolio_recovered["AAPL"], 15000.0)

        # Cash rebuilt: initial 5000 + 2000 + 3000 = 10000
        self.assertEqual(portfolio_recovered["SGOV"], 10000.0)

        # State marked as recovered
        self.assertTrue(self.rm.load_state()["recovered"])

    def test_already_recovered_no_action(self):
        # Set to recovered
        self.rm.save_state({"bottom": 100.0, "recovered": True})

        # Even if price is high enough, we shouldn't trigger again
        market_snapshot = {"price": 130.0, "drawdown": -0.05}
        portfolio_after = self.rm.trim_and_rebalance(
            self.portfolio.copy(), market_snapshot
        )

        # Unchanged
        self.assertEqual(portfolio_after["SMH"], 10000.0)


if __name__ == "__main__":
    unittest.main()

import unittest
from unittest.mock import patch
from src.engine.trades import TradeEngine


class TestTradeEngine(unittest.TestCase):
    def setUp(self):
        self.mock_config = {
            "deployment": {"levels": {"Level 1": 0.1, "Level 2": 0.2}},
            "buy_targets": {
                "Level 1": {"FZROX": 0.5, "SCHD": 0.5},
                "Level 2": {"FZROX": 1.0},
            },
            "funding": {"priority": ["SGOV", "FDRXX"]},
            "limits": {
                "max_position_pct": 0.2,
                "overrides": {"NVDA": 0.3},
                "stock_bucket": ["AAPL", "NVDA"],
            },
            "system": {"files": {"trades": "test_trades.csv"}},
        }
        self.te = TradeEngine(self.mock_config)

    def test_total_value(self):
        portfolio = {"AAPL": 100, "GOOG": 200, "CASH": 50}
        self.assertEqual(self.te.total_value(portfolio), 350)

    def test_apply_position_limits(self):
        portfolio = {"AAPL": 10, "FZROX": 40}  # total = 50
        # max_pct = 0.2, so limit is 10
        # FZROX current = 40 (already over limit)
        self.assertEqual(self.te.apply_position_limits(portfolio, "FZROX", 10), 0)

        # AAPL current = 10, limit = 10
        self.assertEqual(self.te.apply_position_limits(portfolio, "AAPL", 5), 0)

        # New asset SCHD, limit = 10
        self.assertEqual(self.te.apply_position_limits(portfolio, "SCHD", 5), 5)
        self.assertEqual(self.te.apply_position_limits(portfolio, "SCHD", 15), 10)

    def test_generate_crash_trades(self):
        portfolio = {"SGOV": 500, "FDRXX": 500}  # total = 1000
        # Level 1 deployment = 0.1 * 1000 = 100
        # Funding order: SGOV, FDRXX
        # Buy targets: FZROX 0.5, SCHD 0.5
        # Limits: 0.2 of 1000 = 200
        deploy_amt, sells, buys = self.te.generate_crash_trades("Level 1", portfolio)

        self.assertEqual(deploy_amt, 100)
        self.assertIn(("SGOV", 100.0), sells)
        self.assertEqual(len(sells), 1)

        # Buys: 100 * 0.5 = 50 for FZROX and SCHD
        buy_dict = dict(buys)
        self.assertEqual(buy_dict["FZROX"], 50.0)
        self.assertEqual(buy_dict["SCHD"], 50.0)

    def test_apply_trades(self):
        portfolio = {"SGOV": 500, "FZROX": 0}
        sells = [("SGOV", 100.0)]
        buys = [("FZROX", 100.0)]
        new_portfolio = self.te.apply_trades(portfolio.copy(), sells, buys)
        self.assertEqual(new_portfolio["SGOV"], 400.0)
        self.assertEqual(new_portfolio["FZROX"], 100.0)

    @patch("src.engine.trades.TradeEngine.log_trades")
    def test_execute_crash(self, mock_log):
        portfolio = {"SGOV": 1000}
        # Level 1 deployment is 100
        result = self.te.execute_crash("Level 1", portfolio)

        self.assertEqual(result["level"], "Level 1")
        self.assertEqual(result["deploy_amount"], 100.0)
        self.assertEqual(len(result["sells"]), 1)
        self.assertEqual(len(result["buys"]), 2)  # FZROX, SCHD
        self.assertEqual(result["portfolio"]["SGOV"], 900.0)

        self.assertEqual(mock_log.call_count, 2)


if __name__ == "__main__":
    unittest.main()

import unittest
from unittest.mock import MagicMock
from engine.trade_engine import TradeEngine, ITradeLogger
from models.trade import Trade

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
        # Inject a mock logger to comply with Dependency Inversion Principle
        self.mock_logger = MagicMock(spec=ITradeLogger)
        self.te = TradeEngine(self.mock_config, logger=self.mock_logger)

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
        self.assertEqual(sells[0].symbol, "SGOV")
        self.assertEqual(sells[0].action, "SELL")
        self.assertEqual(sells[0].amount, 100.0)
        self.assertEqual(len(sells), 1)

        # Buys: 100 * 0.5 = 50 for FZROX and SCHD
        self.assertEqual(buys[0].symbol, "FZROX")
        self.assertEqual(buys[0].action, "BUY")
        self.assertEqual(buys[0].amount, 50.0)

        self.assertEqual(buys[1].symbol, "SCHD")
        self.assertEqual(buys[1].action, "BUY")
        self.assertEqual(buys[1].amount, 50.0)


    def test_execute_crash_calls_logger(self):
        """Verifies that the engine orchestrates logging through the injected dependency."""
        portfolio = {"SGOV": 1000}
        
        # Execute
        result = self.te.execute_crash("Level 1", portfolio)

        # Verify results
        self.assertEqual(result["level"], "Level 1")
        self.assertEqual(result["deploy_amount"], 100.0)
        self.assertEqual(result["portfolio"]["SGOV"], 1000)

        # Verify the Dependency was utilized correctly (DIP/SRP check)
        self.assertEqual(self.mock_logger.log_trades.call_count, 2)
        
        # Check first call (Sells)
        first_call_args = self.mock_logger.log_trades.call_args_list[0]
        logged_sells = first_call_args[0][0]

        self.assertEqual(len(logged_sells), 1)
        self.assertEqual(logged_sells[0].symbol, "SGOV")
        self.assertEqual(logged_sells[0].action, "SELL")
        self.assertEqual(logged_sells[0].amount, 100.0)

        self.assertEqual(first_call_args[0][1], "Level 1")

    def test_generate_crash_trades_returns_trade_objects(self):
        from models.trade import Trade

        portfolio = {"SGOV": 500, "FDRXX": 500}

        deploy_amt, sells, buys = self.te.generate_crash_trades(
            "Level 1",
            portfolio,
        )

        self.assertEqual(deploy_amt, 100)

        self.assertTrue(all(isinstance(trade, Trade) for trade in sells))
        self.assertTrue(all(isinstance(trade, Trade) for trade in buys))

        self.assertEqual(sells[0].symbol, "SGOV")
        self.assertEqual(sells[0].action, "SELL")
        self.assertEqual(sells[0].amount, 100)

        self.assertEqual(buys[0].symbol, "FZROX")
        self.assertEqual(buys[0].action, "BUY")
        self.assertEqual(buys[0].amount, 50)

    def test_generate_trade_plan(self):
        portfolio = {"SGOV": 500, "FDRXX": 500}

        plan = self.te.generate_trade_plan(
            "Level 1",
            portfolio,
        )

        self.assertEqual(plan.deployment_amount, 100.0)
        self.assertEqual(plan.reason, "Level 1")

        # SELL side
        self.assertEqual(len(plan.sells), 1)
        self.assertEqual(plan.sells[0].symbol, "SGOV")
        self.assertEqual(plan.sells[0].action, "SELL")
        self.assertEqual(plan.sells[0].amount, 100.0)

        # BUY side
        self.assertEqual(len(plan.buys), 2)

        self.assertEqual(plan.buys[0].symbol, "FZROX")
        self.assertEqual(plan.buys[0].action, "BUY")
        self.assertEqual(plan.buys[0].amount, 50.0)

        self.assertEqual(plan.buys[1].symbol, "SCHD")
        self.assertEqual(plan.buys[1].action, "BUY")
        self.assertEqual(plan.buys[1].amount, 50.0)

    def test_generate_trade_plan_returns_trade_plan(self):
        from models.trade_plan import TradePlan

        portfolio = {
            "SGOV": 500,
            "FDRXX": 500,
        }

        plan = self.te.generate_trade_plan(
            "Level 1",
            portfolio,
        )

        self.assertIsInstance(plan, TradePlan)

    def test_execute_crash_uses_trade_plan(self):
        portfolio = {
            "SGOV": 1000,
        }

        plan = self.te.generate_trade_plan(
            "Level 1",
            portfolio,
        )

        result = self.te.execute_crash(
            "Level 1",
            {"SGOV": 1000},
        )

        self.assertEqual(
            result["deploy_amount"],
            plan.deployment_amount,
        )

        self.assertEqual(
            result["sells"],
            plan.sells,
        )

        self.assertEqual(
            result["buys"],
            plan.buys,
        )

    def test_execute_crash_does_not_modify_portfolio(self):

        portfolio = {
            "SGOV": 1000,
        }

        original_portfolio = portfolio.copy()

        self.te.execute_crash(
            "Level 1",
            portfolio,
        )

        self.assertEqual(portfolio, original_portfolio)

    def test_generate_trade_plan_does_not_modify_portfolio(self):
        portfolio = {
            "SGOV": 500,
            "FDRXX": 500,
        }

        original_portfolio = portfolio.copy()

        self.te.generate_trade_plan(
            "Level 1",
            portfolio,
        )

        self.assertEqual(portfolio, original_portfolio)


if __name__ == "__main__":
    unittest.main()

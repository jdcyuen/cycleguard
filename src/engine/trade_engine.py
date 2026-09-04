# tradepy

import csv
from datetime import datetime
from abc import ABC, abstractmethod

# from config.config_loader import ConfigLoader
from config.config_manager import get_config

from models.trade import Trade
from models.trade_plan import TradePlan
from engine.trade_logger_interface import ITradeLogger


# -------------------------
# ENGINE (SRP / OCP / DIP)
# -------------------------
class TradeEngine:
    """Responsible ONLY for calculating and orchestrating trades."""

    def __init__(self, config=None, logger: ITradeLogger = None):
        # self.config = config if config else ConfigLoader().load()
        self.config = config if config else get_config()
        self.deployment = self.config["deployment"]["levels"]
        self.buy_targets = self.config["buy_targets"]
        self.funding_order = self.config["funding"]["priority"]
        self.limits = self.config["limits"]
        self.stock_bucket = self.config["limits"]["stock_bucket"]

        # Dependency Injection (DIP)
        if logger:
            self.logger = logger
        else:
            # Sensible default
            log_path = self.config["system"]["files"]["trades"]
            self.logger = CSVTradeLogger(log_path)

    def total_value(self, portfolio):
        return sum(portfolio.values())

    def apply_position_limits(self, portfolio, ticker, amount):
        total = self.total_value(portfolio)
        max_pct = self.limits.get("max_position_pct", 0.10)
        overrides = self.limits.get("overrides", {})
        limit = overrides.get(ticker, max_pct)

        current_value = portfolio.get(ticker, 0)
        max_allowed = total * limit
        remaining_capacity = max_allowed - current_value

        return max(0, min(amount, remaining_capacity))

    def generate_crash_trades(self, level, portfolio):
        deploy_pct = self.deployment[level]
        total = self.total_value(portfolio)
        deploy_amount = total * deploy_pct

        # SELL SIDE (FUNDING)
        sells = []
        remaining = deploy_amount

        for asset in self.funding_order:
            available = portfolio.get(asset, 0)
            sell_amt = min(available, remaining)

            if sell_amt > 0:
                sell_amt = round(sell_amt, 2)
                sells.append(
                    Trade(
                        symbol=asset,
                        action="SELL",
                        amount=sell_amt,
                    )
                )
                remaining -= sell_amt

            if remaining <= 0:
                break

        # BUY SIDE
        buys = []
        targets = self.buy_targets[level]

        for ticker, weight in targets.items():
            amount = deploy_amount * weight

            if ticker == "STOCKS":
                split = amount / len(self.stock_bucket)
                for s in self.stock_bucket:
                    adj_amount = self.apply_position_limits(portfolio, s, split)
                    if adj_amount > 0:
                        buys.append(
                            Trade(
                                symbol=s,
                                action="BUY",
                                amount=round(adj_amount, 2),
                            )
                        )
            else:
                adj_amount = self.apply_position_limits(portfolio, ticker, amount)
                if adj_amount > 0:
                    buys.append(
                        Trade(
                            symbol=ticker,
                            action="BUY",
                            amount=round(adj_amount, 2),
                        )
                    )

        return deploy_amount, sells, buys

    def generate_trade_plan(self, level, portfolio):

        deploy_amount, sells, buys = self.generate_crash_trades(
            level,
            portfolio,
        )

        return TradePlan(
            deployment_amount=deploy_amount,
            reason=level,
            sells=sells,
            buys=buys,
        )

    def execute_crash(self, level, portfolio):

        """Orchestrates the crash deployment and records history."""
        plan = self.generate_trade_plan(
            level,
            portfolio,
        )

        # Log trades via the injected logger
        if self.logger:

            self.logger.log_trades(
                plan.sells,
                plan.reason,
            )

            self.logger.log_trades(
                plan.buys,
                plan.reason,
            )

        return {
            "level": level,
            "deploy_amount": plan.deployment_amount,
            "sells": plan.sells,
            "buys": plan.buys,
            "portfolio": portfolio,
        }

    def remaining_dry_powder(self, portfolio):
        return sum(portfolio.get(x, 0) for x in self.funding_order)

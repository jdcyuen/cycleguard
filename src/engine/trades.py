# trades.py

import csv
from datetime import datetime
from src.config.config_loader import load_config


class TradeEngine:
    def __init__(self, config=None):
        self.config = config if config else load_config()
        self.deployment = self.config["deployment"]["levels"]
        self.buy_targets = self.config["buy_targets"]
        self.funding_order = self.config["funding"]["priority"]
        self.limits = self.config["limits"]
        self.stock_bucket = self.config["limits"]["stock_bucket"]
        self.trade_log = self.config["system"]["files"]["trades"]

    # =========================
    # CALCULATE TOTAL PORTFOLIO
    # =========================
    def total_value(self, portfolio):
        return sum(portfolio.values())

    # =========================
    # POSITION LIMIT CHECK
    # =========================
    def apply_position_limits(self, portfolio, ticker, amount):
        total = self.total_value(portfolio)

        max_pct = self.limits.get("max_position_pct", 0.10)
        overrides = self.limits.get("overrides", {})

        limit = overrides.get(ticker, max_pct)

        current_value = portfolio.get(ticker, 0)
        max_allowed = total * limit

        remaining_capacity = max_allowed - current_value

        return max(0, min(amount, remaining_capacity))

    # =========================
    # GENERATE CRASH TRADES
    # =========================
    def generate_crash_trades(self, level, portfolio):
        deploy_pct = self.deployment[level]
        total = self.total_value(portfolio)
        deploy_amount = total * deploy_pct

        # -------------------------
        # SELL SIDE (FUNDING)
        # -------------------------
        sells = []
        remaining = deploy_amount

        for asset in self.funding_order:
            available = portfolio.get(asset, 0)
            sell_amt = min(available, remaining)

            if sell_amt > 0:
                sell_amt = round(sell_amt, 2)
                sells.append((asset, sell_amt))
                remaining -= sell_amt

            if remaining <= 0:
                break

        # -------------------------
        # BUY SIDE
        # -------------------------
        buys = []
        targets = self.buy_targets[level]

        for ticker, weight in targets.items():
            amount = deploy_amount * weight

            if ticker == "STOCKS":
                split = amount / len(self.stock_bucket)
                for s in self.stock_bucket:
                    adj_amount = self.apply_position_limits(portfolio, s, split)
                    if adj_amount > 0:
                        buys.append((s, round(adj_amount, 2)))
            else:
                adj_amount = self.apply_position_limits(portfolio, ticker, amount)
                if adj_amount > 0:
                    buys.append((ticker, round(adj_amount, 2)))

        return deploy_amount, sells, buys

    # =========================
    # APPLY TRADES
    # =========================
    def apply_trades(self, portfolio, sells, buys):
        # Apply sells
        for asset, amt in sells:
            portfolio[asset] = round(portfolio.get(asset, 0) - amt, 2)

        # Apply buys
        for asset, amt in buys:
            portfolio[asset] = round(portfolio.get(asset, 0) + amt, 2)

        return portfolio

    # =========================
    # LOG TRADES
    # =========================
    def log_trades(self, trades, trade_type, reason):
        with open(self.trade_log, "a", newline="") as f:
            writer = csv.writer(f)

            for asset, amt in trades:
                writer.writerow(
                    [
                        datetime.now().strftime("%Y-%m-%d"),
                        asset,          # symbol
                        trade_type,     # action
                        round(amt, 2),  # amount
                        reason,         # signal type
                    ]
                )

    # =========================
    # EXECUTE CRASH LEVEL
    # =========================
    def execute_crash(self, level, portfolio):
        deploy_amount, sells, buys = self.generate_crash_trades(level, portfolio)

        # Log trades
        self.log_trades(sells, "SELL", level)
        self.log_trades(buys, "BUY", level)

        # Apply trades
        portfolio = self.apply_trades(portfolio, sells, buys)

        return {
            "level": level,
            "deploy_amount": deploy_amount,
            "sells": sells,
            "buys": buys,
            "portfolio": portfolio,
        }

    # =========================
    # DRY POWDER
    # =========================
    def remaining_dry_powder(self, portfolio):
        return sum(portfolio.get(x, 0) for x in self.funding_order)

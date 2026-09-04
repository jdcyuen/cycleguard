
import csv
from datetime import datetime
from engine.trade_logger_interface import ITradeLogger


# -------------------------
# IMPLEMENTATION (SRP)
# -------------------------
class CSVTradeLogger(ITradeLogger):
    """Responsible ONLY for persisting trades to a CSV file."""

    def __init__(self, log_path):
        self.log_path = log_path

    def log_trades(self, trades, reason):

        with open(self.log_path, "a", newline="") as f:
            writer = csv.writer(f)

            for trade in trades:
                writer.writerow(
                    [
                        datetime.now().strftime("%Y-%m-%d"),
                        trade.symbol,
                        trade.action,
                        round(trade.amount, 2),
                        reason,
                    ]
                )
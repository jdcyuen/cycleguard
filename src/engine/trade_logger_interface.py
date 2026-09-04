
from abc import ABC, abstractmethod


# -------------------------
# INTERFACE (DIP)
# -------------------------
class ITradeLogger(ABC):
    """Abstract interface for trade logging."""

    @abstractmethod
    def log_trades(self, trades: list, reason: str):
        pass

from abc import ABC, abstractmethod
from typing import Any


class MarketSignal(ABC):
    """
    Base contract for all CycleGuard market regime signals.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the unique name of the signal."""
        raise NotImplementedError

    @abstractmethod
    def evaluate(self, data: Any) -> dict:
        """
        Evaluate the signal using supplied market data.

        Returns:
            A dictionary containing the signal result.
        """
        raise NotImplementedError
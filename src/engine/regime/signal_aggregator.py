from typing import Iterable

from .signals.base import MarketSignal


class SignalAggregator:
    """
    Evaluates a collection of market signals.

    The aggregator is responsible only for coordinating signal evaluation.
    It does not interpret the results or determine a market regime.
    """

    def __init__(self, signals: Iterable[MarketSignal]):
        self.signals = list(signals)

    def evaluate(self, data: dict) -> dict:
        """
        Evaluate all configured signals.

        Returns:
            Dictionary keyed by signal name containing each signal's result.
        """
        results = {}

        for signal in self.signals:
            results[signal.name] = signal.evaluate(data)

        return results
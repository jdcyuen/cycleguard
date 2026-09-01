from engine.regime.signal_aggregator import SignalAggregator
from engine.regime.signals.base import MarketSignal


class DummySignal(MarketSignal):
    def __init__(self, signal_name, status):
        self._name = signal_name
        self.status = status

    @property
    def name(self):
        return self._name

    def evaluate(self, data):
        return {
            "name": self.name,
            "status": self.status,
        }


def test_aggregator_evaluates_all_signals():
    signals = [
        DummySignal("trend", "Bullish"),
        DummySignal("volatility", "Calm"),
    ]

    aggregator = SignalAggregator(signals)

    result = aggregator.evaluate({"market": "data"})

    assert result["trend"]["status"] == "Bullish"
    assert result["volatility"]["status"] == "Calm"


def test_aggregator_returns_empty_result_when_no_signals():
    aggregator = SignalAggregator([])

    result = aggregator.evaluate({})

    assert result == {}


def test_aggregator_uses_signal_name_as_key():
    signal = DummySignal("cape", "Expensive")

    aggregator = SignalAggregator([signal])

    result = aggregator.evaluate({})

    assert "cape" in result
    assert result["cape"]["name"] == "cape"


def test_aggregator_passes_data_to_signal():
    class DataCaptureSignal(MarketSignal):
        @property
        def name(self):
            return "capture"

        def evaluate(self, data):
            return {
                "received": data,
            }

    market_data = {"latest": {"SPY": 500}}

    aggregator = SignalAggregator([DataCaptureSignal()])

    result = aggregator.evaluate(market_data)

    assert result["capture"]["received"] is market_data
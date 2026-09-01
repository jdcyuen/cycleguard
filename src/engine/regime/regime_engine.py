from .regime_classifier import RegimeClassifier
from .signal_aggregator import SignalAggregator
from .signal_factory import SignalFactory


class RegimeEngine:
    """Coordinates signal evaluation and regime classification."""

    def __init__(self, config: dict):
        self.config = config

        signal_configs = config.get("signals", {})

        signals = [
            SignalFactory.create(name, signal_config)
            for name, signal_config in signal_configs.items()
        ]

        self.aggregator = SignalAggregator(signals)
        self.classifier = RegimeClassifier(config)

    def evaluate(self, data: dict) -> dict:
        """Evaluate signals and classify the resulting market regime."""
        signal_results = self.aggregator.evaluate(data)
        regime = self.classifier.classify(signal_results)

        return {
            "signals": signal_results,
            "regime": regime,
        }
from typing import Any


class RegimeClassifier:
    """
    Determines the market regime from evaluated signal results.

    The classifier does not evaluate individual signals. It only applies
    configured regime conditions to already-evaluated signal results.
    """

    def __init__(self, regime_config: dict[str, Any]):
        self.regimes = regime_config.get("regimes", {})
        self.fallback_regime = regime_config.get(
            "fallback_regime",
            "TRANSITION",
        )

    def classify(self, signal_results: dict[str, dict]) -> str:
        """
        Classify the market based on signal results.

        A regime matches only when all of its configured conditions match.
        Regimes are evaluated in YAML/configuration order.
        """
        for regime_name, regime_definition in self.regimes.items():
            conditions = regime_definition.get("conditions", {})

            if self._conditions_match(conditions, signal_results):
                return regime_name

        return self.fallback_regime

    @staticmethod
    def _conditions_match(
        conditions: dict[str, str],
        signal_results: dict[str, dict],
    ) -> bool:
        """Return True when every configured condition matches."""
        for signal_name, expected_status in conditions.items():
            signal = signal_results.get(signal_name)

            if not signal:
                return False

            actual_status = signal.get("status")

            if actual_status != expected_status:
                return False

        return True
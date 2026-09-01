from engine.regime.signals.base import MarketSignal


class VolatilitySignal(MarketSignal):
    """
    Evaluates market volatility using the VIX.
    """

    def __init__(self, config=None):
        self.config = config or {}

        thresholds = self.config.get("thresholds", {})

        self.calm_threshold = thresholds.get("calm", 18)
        self.risk_off_threshold = thresholds.get(
            "elevated",
            thresholds.get("stress", 25),
        )

    @property
    def name(self) -> str:
        return "volatility"

    def evaluate(self, data: dict) -> dict:
        current_vix = data["value"]

        if current_vix < self.calm_threshold:
            status = "calm"
        elif current_vix > self.risk_off_threshold:
            status = "risk-off"
        else:
            status = "neutral"

        return {
            "status": status,
            "value": current_vix,
        }
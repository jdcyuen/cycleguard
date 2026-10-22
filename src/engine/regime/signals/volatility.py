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
        latest = data.get("latest", {})

        if latest:
            if not self.config.get("inputs"):
                return {
                    "status": "unknown",
                    "value": None,
                }

            vix_proxy = self.config["inputs"][0]

            if vix_proxy not in latest:
                return {
                    "status": "unknown",
                    "value": None,
                }

            current_vix = latest[vix_proxy]

        else:
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
            "evidence": {
                "raw_inputs": {
                    "value": current_vix,
                },
                "calculated_values": {
                    "status": status,
                },
                "thresholds": {
                    "calm": self.calm_threshold,
                    "elevated": self.risk_off_threshold,
                },
                "rule": (
                    "< 18 Calm Low market stress; "
                    "> 25 Risk-Off High market stress; "
                    "18 - 25 neutral Elevated but not extreme."
                ),
                "why": (
                    f"VIX is {current_vix}. "
                    f"Calm threshold is {self.calm_threshold}; "
                    f"elevated threshold is {self.risk_off_threshold}; "
                    f"result is {status}."
                ),
            },
        }
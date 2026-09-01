from .base import MarketSignal


class CapeSignal(MarketSignal):
    """Evaluates market valuation using the CAPE ratio."""

    def __init__(self, config):
        self.inputs = config.get("inputs", [])
        self.thresholds = config.get("thresholds", {})

    @property
    def name(self) -> str:
        return "cape"

    def evaluate(self, data):
        if len(self.inputs) != 1:
            return {
                "name": self.name,
                "status": "unknown",
            }

        input_name = self.inputs[0]
        latest = data.get("latest", {})

        if input_name not in latest:
            return {
                "name": self.name,
                "status": "unknown",
            }

        value = latest[input_name]

        expensive = self.thresholds.get("expensive", 30)
        neutral = self.thresholds.get("neutral", 25)
        cheap = self.thresholds.get("cheap", 20)

        if value >= expensive:
            status = "expensive"
        elif value >= neutral:
            status = "neutral"
        elif value >= cheap:
            status = "attractive"
        else:
            status = "cheap"

        return {
            "name": self.name,
            "status": status,
            "input": input_name,
            "value": value,
        }
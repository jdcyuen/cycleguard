from .base import MarketSignal


class CreditSignal(MarketSignal):
    """Evaluates credit conditions using configured inputs."""

    def __init__(self, config):
        self.inputs = config.get("inputs", [])

    @property
    def name(self) -> str:
        return "credit"

    def evaluate(self, data):
        latest = data.get("latest", {})
        dma50 = data.get("dma50", {})

        if len(self.inputs) != 2:
            return {
                "name": self.name,
                "status": "Unknown",
            }

        first, second = self.inputs

        if (
            first not in latest
            or second not in latest
            or first not in dma50
            or second not in dma50
        ):
            return {
                "name": self.name,
                "status": "Unknown",
            }

        current_ratio = latest[first] / latest[second]
        ratio_50 = dma50[first] / dma50[second]

        status = "Healthy" if current_ratio > ratio_50 else "Stressed"

        return {
            "name": self.name,
            "status": status,
            "inputs": self.inputs,
            "ratio_current": current_ratio,
            "ratio_50": ratio_50,
        }
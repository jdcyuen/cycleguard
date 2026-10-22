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
            "evidence": {
                "raw_inputs": {
                    "latest": {
                        first: latest[first],
                        second: latest[second],
                    },
                    "dma50": {
                        first: dma50[first],
                        second: dma50[second],
                    },
                },
                "calculated_values": {
                    "ratio_current": current_ratio,
                    "ratio_50": ratio_50,
                    "status": status,
                },
                "comparison": {
                    "first": first,
                    "second": second,
                    "current_ratio": current_ratio,
                    "sma50_ratio": ratio_50,
                    "status": status.upper(),
                },
                "rule": (
                    "Healthy when the current first-to-second ratio is above "
                    "the 50-day SMA ratio; otherwise Stressed."
                ),
                "why": (
                    f"{first}/{second} current ratio is {current_ratio:.4f}, "
                    f"versus the 50-day ratio of {ratio_50:.4f}; "
                    f"result is {status}."
                ),
            },
        }
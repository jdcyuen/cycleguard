from .base import MarketSignal


class LeadershipSignal(MarketSignal):
    """Evaluates market leadership across configured inputs."""

    def __init__(self, config):
        self.inputs = config.get("inputs", [])

    @property
    def name(self) -> str:
        return "leadership"

    def evaluate(self, data):
        latest = data.get("latest", {})
        dma50 = data.get("dma50", {})

        if not self.inputs:
            return {
                "name": self.name,
                "status": "Unknown",
            }

        valid_inputs = [
            symbol
            for symbol in self.inputs
            if symbol in latest and symbol in dma50
        ]

        if not valid_inputs:
            return {
                "name": self.name,
                "status": "Unknown",
            }

        above_50 = sum(
            latest[symbol] > dma50[symbol]
            for symbol in valid_inputs
        )

        if above_50 == len(valid_inputs):
            status = "Strong"
        elif above_50 == 0:
            status = "Weak"
        else:
            status = "Mixed"

        return {
            "name": self.name,
            "status": status,
            "inputs": valid_inputs,
            "above_50": above_50,
            "total": len(valid_inputs),
            "evidence": {
                "raw_inputs": {
                    "latest": {
                        symbol: latest[symbol]
                        for symbol in valid_inputs
                    },
                    "dma50": {
                        symbol: dma50[symbol]
                        for symbol in valid_inputs
                    },
                },
                "calculated_values": {
                    "above_50": above_50,
                    "total": len(valid_inputs),
                    "status": status,
                },
                "rule": (
                    "Strong when all valid leadership inputs are above "
                    "their 50-day SMA; Weak when none are above; "
                    "otherwise Mixed."
                ),
                "why": (
                    f"{above_50} of {len(valid_inputs)} leadership "
                    f"inputs are above their 50-day SMA."
                ),
            },
        }
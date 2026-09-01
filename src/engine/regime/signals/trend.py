from engine.regime.signals.base import MarketSignal


class TrendSignal(MarketSignal):

    """
    Evaluates broad-market trend using price relative to moving averages.
    """

    def __init__(self, config=None):
        self.config = config or {}

        inputs = self.config.get(
            "inputs",
            ["SPY"],
        )

        self.proxy = inputs[0]

    @property
    def name(self) -> str:
        return "trend"

    def evaluate(self, data: dict) -> dict:
        latest = data.get("latest")
        dma50_data = data.get("dma50")
        dma200_data = data.get("dma200")

        # Backward-compatible scalar input
        if latest is None:
            current = data["current"]
            dma50_value = data["dma50"]
            dma200_value = data["dma200"]

        # Normalized engine input
        else:
            current = latest[self.proxy]
            dma50_value = dma50_data[self.proxy]
            dma200_value = dma200_data[self.proxy]

        if current > dma200_value:
            status = "bullish"
        elif min(dma50_value, dma200_value) <= current <= max(
            dma50_value,
            dma200_value,
        ):
            status = "neutral"
        else:
            status = "bearish"

        return {
            "status": status,
            "proxy": self.proxy,
            "value": current,
            "dma50": dma50_value,
            "dma200": dma200_value,
        }
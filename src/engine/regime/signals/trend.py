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

        if min(dma50_value, dma200_value) <= current <= max(
            dma50_value,
            dma200_value,
        ):
            status = "neutral"
        elif current > max(dma50_value, dma200_value):
            status = "bullish"
        else:
            status = "bearish"

        return {
            "status": status,
            "proxy": self.proxy,
            "value": current,
            "dma50": dma50_value,
            "dma200": dma200_value,
            "evidence": {
                "raw_inputs": {
                    "current": current,
                },
                "calculated_values": {
                    "dma50": dma50_value,
                    "dma200": dma200_value,
                },
                "comparison": {
                    "proxy": self.proxy,
                    "current": current,
                    "sma50": dma50_value,
                    "sma200": dma200_value,
                    "status": status.upper(),
                },
                "rule": (
                    "Bullish when current price is above both the 50-day and 200-day SMAs; "
                    "neutral when price is between the 50-day and 200-day SMAs; "
                    "otherwise bearish."
                ),
                "why": (
                    f"{self.proxy} current price is {current}, "
                    f"50-day SMA is {dma50_value}, "
                    f"and 200-day SMA is {dma200_value}; "
                    f"price is {status} based on its position relative to both moving averages."
                ),
            },
        }
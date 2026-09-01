from engine.regime.signals.base import MarketSignal


class BreadthSignal(MarketSignal):
    """
    Evaluates market breadth using the percentage of configured
    securities trading above their 50-day moving average.
    """

    DEFAULT_PROXIES = [
        "XLC",
        "XLY",
        "XLP",
        "XLE",
        "XLF",
        "XLV",
        "XLI",
        "XLB",
        "XLRE",
        "XLK",
        "XLU",
    ]

    def __init__(self, config=None):
        self.config = config or {}

        self.proxies = self.config.get(
            "inputs",
            self.DEFAULT_PROXIES.copy(),
        )

        thresholds = self.config.get("thresholds", {})

        self.strong_threshold = thresholds.get("strong", 65)
        self.neutral_threshold = thresholds.get("neutral", 50)
        self.weak_threshold = thresholds.get("weak", 35)

    @property
    def name(self) -> str:
        return "breadth"

    def evaluate(self, data: dict) -> dict:
        latest = data["latest"]
        dma50 = data["dma50"]

        passing = []
        failing = []
        valid_total = 0

        for proxy in self.proxies:
            if (
                proxy in latest
                and proxy in dma50
                and not latest[proxy] != latest[proxy]
                and not dma50[proxy] != dma50[proxy]
            ):
                valid_total += 1

                if latest[proxy] > dma50[proxy]:
                    passing.append(proxy)
                else:
                    failing.append(proxy)

        if valid_total == 0:
            return {
                "status": "Unknown",
                "value": 0,
                "passing": [],
                "failing": [],
                "valid_total": 0,
            }

        pct_above_50 = (len(passing) / valid_total) * 100

        if pct_above_50 > self.strong_threshold:
            status = "Strong"
        elif pct_above_50 >= self.weak_threshold:
            status = "Improving"
        else:
            status = "Weak"

        return {
            "status": status,
            "value": pct_above_50,
            "passing": passing,
            "failing": failing,
            "valid_total": valid_total,
        }
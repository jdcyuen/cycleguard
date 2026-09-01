from .signals.trend import TrendSignal
from .signals.breadth import BreadthSignal
from .signals.volatility import VolatilitySignal
from .signals.leadership import LeadershipSignal
from .signals.credit import CreditSignal
from .signals.cape import CapeSignal


class SignalFactory:
    """Creates market signal instances from configuration."""

    _SIGNALS = {
        "trend": TrendSignal,
        "breadth": BreadthSignal,
        "volatility": VolatilitySignal,
        "leadership": LeadershipSignal,
        "credit": CreditSignal,
        "cape": CapeSignal,
    }

    @classmethod
    def create(cls, name: str, config: dict):
        """Create a configured market signal."""
        try:
            signal_class = cls._SIGNALS[name]
        except KeyError:
            raise ValueError(f"Unknown signal: {name}")

        return signal_class(config)
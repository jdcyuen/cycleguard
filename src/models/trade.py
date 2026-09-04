from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Trade:
    """A proposed BUY or SELL transaction."""

    symbol: str
    action: str
    amount: Decimal
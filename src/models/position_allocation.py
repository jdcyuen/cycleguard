from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class PositionAllocation:
    """
    Represents a position's allocation within a portfolio bucket.
    """

    symbol: str
    bucket: str
    market_value: Decimal
    weight: Decimal
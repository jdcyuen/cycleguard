from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class PortfolioBucket:
    """
    Represents the current allocation of a portfolio bucket.
    """

    name: str
    market_value: Decimal
    weight: Decimal
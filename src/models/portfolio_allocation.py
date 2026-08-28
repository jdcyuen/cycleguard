from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class PortfolioAllocation:
    """
    Represents the aggregated allocation of a portfolio.
    """

    portfolio_value: Decimal
    buckets: dict[str, object]
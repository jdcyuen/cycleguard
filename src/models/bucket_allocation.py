from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class BucketAllocation:
    """
    Represents actual and target allocation for a portfolio bucket.
    """

    name: str
    market_value: Decimal
    actual_weight: Decimal
    target_weight: Decimal
    drift: Decimal
    drift_value: Decimal
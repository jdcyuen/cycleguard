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
	
	#drift tells you how far a bucket's allocation is from its target
    drift: Decimal
	
	#drift value translates that difference into dollars.
    drift_value: Decimal
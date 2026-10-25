
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class BucketTrimProposal:
    """Represents a proposed trim for an overweight portfolio bucket."""

    bucket_name: str
    actual_weight: Decimal
    target_weight: Decimal
    upper_boundary: Decimal
    trim_amount: Decimal

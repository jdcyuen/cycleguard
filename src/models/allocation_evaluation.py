from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class AllocationEvaluation:
    """
    Represents the desired portfolio allocation.
    AllocationEvaluation is the container for the portfolio's desired allocation after CycleGuard has applied 
    its allocation rules.

    For Example:

    AllocationEvaluation(
        top_level_targets={
            "equity": Decimal("0.50"),
            "income": Decimal("0.45"),
            "alternatives": Decimal("0.05"),
        },

        bucket_targets={
            "core_equity": Decimal("0.20"),
            "equity_growth": Decimal("0.10"),
            "fixed_income": Decimal("0.30"),
        },

        security_targets={
            "FTEC": Decimal("0.07"),
            "AAPL": Decimal("0.018"),
            "SPMO": Decimal("0.012"),
        },
    )
    """

    top_level_targets: dict[str, Decimal]
    bucket_targets: dict[str, Decimal]
    security_targets: dict[str, Decimal]
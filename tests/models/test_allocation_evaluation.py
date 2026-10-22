from decimal import Decimal

from models.allocation_evaluation import AllocationEvaluation


def test_allocation_evaluation_stores_targets():
    evaluation = AllocationEvaluation(
        top_level_targets={
            "equity": Decimal("0.50"),
            "income": Decimal("0.45"),
            "alternatives": Decimal("0.05"),
        },
        bucket_targets={
            "core_equity": Decimal("0.20"),
            "equity_growth": Decimal("0.08"),
        },
        security_targets={
            "FTEC": Decimal("0.07"),
            "AAPL": Decimal("0.01"),
        },
    )

    assert evaluation.top_level_targets["equity"] == Decimal("0.50")
    assert evaluation.bucket_targets["equity_growth"] == Decimal("0.08")
    assert evaluation.security_targets["FTEC"] == Decimal("0.07")
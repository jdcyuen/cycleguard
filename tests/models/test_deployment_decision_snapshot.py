from datetime import date
from decimal import Decimal

from models.deployment_decision_snapshot import DeploymentDecisionSnapshot

def test_deployment_decision_snapshot_can_be_created():
    snapshot = DeploymentDecisionSnapshot(
        deployment_decision_snapshot_id=1,
        deployment_decision_id=10,
        snapshot_date=date(2026, 9, 6),
        recommended_amount=Decimal("25000"),
        actual_amount_deployed=Decimal("10000"),
        )

    assert snapshot.deployment_decision_snapshot_id == 1
    assert snapshot.deployment_decision_id == 10
    assert snapshot.snapshot_date == date(2026, 9, 6)
    assert snapshot.recommended_amount == Decimal("25000")
    assert snapshot.actual_amount_deployed == Decimal("10000")

from decimal import Decimal
from unittest.mock import MagicMock

from models.deployment_decision_snapshot import (
    DeploymentDecisionSnapshot,
)
from services.deployment_decision_snapshot_service import (
    DeploymentDecisionSnapshotService,
)


def test_create_deployment_decision_snapshot():
    repository = MagicMock()
    repository.create.return_value = 123

    service = DeploymentDecisionSnapshotService(repository)

    snapshot = DeploymentDecisionSnapshot(
        deployment_decision_id=10,
        recommended_amount=Decimal("25000"),
        actual_amount_deployed=Decimal("10000"),
    )

    result = service.create(snapshot)

    assert result == 123

    repository.create.assert_called_once_with(snapshot)
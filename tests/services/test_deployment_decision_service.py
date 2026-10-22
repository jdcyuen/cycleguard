from decimal import Decimal
from unittest.mock import MagicMock

from models.deployment_decision import DeploymentDecision
from services.deployment_decision_service import DeploymentDecisionService


def test_create_deployment_decision():
    repository = MagicMock()
    repository.create.return_value = 123

    service = DeploymentDecisionService(repository)

    decision = DeploymentDecision(
        account_number="ABC123",
        recommended_amount=Decimal("25000"),
        reason="Favorable market conditions.",
    )

    result = service.create(decision)

    assert result == 123

    repository.create.assert_called_once_with(decision)
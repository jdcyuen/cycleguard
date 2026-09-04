from services import portfolio_aggregation_service
from services import portfolio_aggregation_service
from services import portfolio_aggregation_service
import pytest
from decimal import Decimal
from unittest.mock import MagicMock

from models.deployment import DeploymentDecision
from services.deployment_orchestration_service import (
    DeploymentOrchestrationService,
)


def test_evaluate_returns_deployment_decision():
    portfolio_service = MagicMock()
    regime_engine = MagicMock()
    regime_deployment_engine = MagicMock()
    crash_manager = MagicMock()
    crash_deployment_engine = MagicMock()

    portfolio_service.get_available_capital.return_value = Decimal("100000")

    regime_engine.evaluate.return_value = {
        "regime": "RISK_ON",
        "signals": {},
    }

    expected_decision = DeploymentDecision(
        action="DEPLOY",
        deployment_pct=Decimal("1.0"),
        deployment_amount=Decimal("100000"),
    )

    regime_deployment_engine.evaluate.return_value = expected_decision

    service = DeploymentOrchestrationService(
    portfolio_service=portfolio_service,
    regime_engine=regime_engine,
    crash_manager=crash_manager,
    regime_deployment_engine=regime_deployment_engine,
    crash_deployment_engine=crash_deployment_engine,
)

    result = service.evaluate(
        snapshot_id=123,
        market_data={"test": "data"},
    )

    assert result is expected_decision

def test_evaluate_gets_available_capital_from_portfolio_service():
    portfolio_service = MagicMock()
    regime_engine = MagicMock()
    regime_deployment_engine = MagicMock()
    crash_manager = MagicMock()
    crash_deployment_engine = MagicMock()

    portfolio_service.get_available_capital.return_value = Decimal("75000")

    regime_engine.evaluate.return_value = {
        "regime": "RISK_ON",
        "signals": {},
    }

    expected_decision = DeploymentDecision(
        action="DEPLOY",
        deployment_pct=Decimal("1.0"),
        deployment_amount=Decimal("75000"),
    )

    regime_deployment_engine.evaluate.return_value = expected_decision

    service = DeploymentOrchestrationService(
        portfolio_service=portfolio_service,
        regime_engine=regime_engine,
        crash_manager=crash_manager,
        regime_deployment_engine=regime_deployment_engine,
        crash_deployment_engine=crash_deployment_engine,
    )

    service.evaluate(
        snapshot_id=456,
        market_data={"test": "data"},
    )

    portfolio_service.get_available_capital.assert_called_once_with(456)

def test_evaluate_passes_market_data_to_regime_engine():
    portfolio_service = MagicMock()
    regime_engine = MagicMock()
    regime_deployment_engine = MagicMock()
    crash_manager = MagicMock()
    crash_deployment_engine = MagicMock()

    portfolio_service.get_available_capital.return_value = Decimal("75000")

    market_data = {
        "sp500": 6500,
        "vix": 15,
    }

    regime_result = {
        "regime": "RISK_ON",
        "signals": {},
    }

    regime_engine.evaluate.return_value = regime_result

    regime_deployment_engine.evaluate.return_value = DeploymentDecision(
        action="DEPLOY",
        deployment_pct=Decimal("1.0"),
        deployment_amount=Decimal("75000"),
    )

    service = DeploymentOrchestrationService(
        portfolio_service=portfolio_service,
        regime_engine=regime_engine,
        crash_manager=crash_manager,
        regime_deployment_engine=regime_deployment_engine,
        crash_deployment_engine=crash_deployment_engine,
    )

    service.evaluate(
        snapshot_id=456,
        market_data=market_data,
    )

    regime_engine.evaluate.assert_called_once_with(market_data)

def test_evaluate_passes_regime_and_capital_to_regime_deployment_engine():

    portfolio_service = MagicMock()
    regime_engine = MagicMock()
    crash_manager = MagicMock()
    regime_deployment_engine = MagicMock()
    crash_deployment_engine = MagicMock()

    available_capital = Decimal("75000")

    regime_result = {
        "regime": "RISK_ON",
        "signals": {},
    }

    portfolio_service.get_available_capital.return_value = available_capital
    regime_engine.evaluate.return_value = regime_result

    expected_decision = DeploymentDecision(
        action="DEPLOY",
        deployment_pct=Decimal("1.0"),
        deployment_amount=Decimal("75000"),
    )

    regime_deployment_engine.evaluate.return_value = expected_decision

    service = DeploymentOrchestrationService(
        portfolio_service=portfolio_service,
        regime_engine=regime_engine,
        crash_manager=crash_manager,
        regime_deployment_engine=regime_deployment_engine,
        crash_deployment_engine=crash_deployment_engine,
    )

    service.evaluate(
        snapshot_id=456,
        market_data={"test": "data"},
    )

    regime_deployment_engine.evaluate.assert_called_once_with(
        regime_result,
        available_capital,
    )

def test_evaluate_rejects_invalid_snapshot_id():
    portfolio_service = MagicMock()
    regime_engine = MagicMock()
    regime_deployment_engine = MagicMock()
    crash_manager = MagicMock()
    crash_deployment_engine = MagicMock()

    service = DeploymentOrchestrationService(
        portfolio_service=portfolio_service,
        regime_engine=regime_engine,
        crash_manager=crash_manager,
        regime_deployment_engine=regime_deployment_engine,
        crash_deployment_engine=crash_deployment_engine,
    )

    with pytest.raises(ValueError, match="Snapshot ID"):
        service.evaluate(
            snapshot_id=None,
            market_data={"test": "data"},
        )

def test_crash_deployment_takes_priority_over_regime_deployment():
    portfolio_service = MagicMock()
    regime_engine = MagicMock()
    crash_manager = MagicMock()
    regime_deployment_engine = MagicMock()
    crash_deployment_engine = MagicMock()

    available_capital = Decimal("100000")

    portfolio_service.get_available_capital.return_value = available_capital

    regime_engine.evaluate.return_value = {
        "regime": "RISK_ON",
        "signals": {},
    }

    crash_manager.run.return_value = {
        "close": 4000,
        "cycle_peak": 5000,
        "drawdown": -0.20,
    }

    regime_decision = DeploymentDecision(
        action="DEPLOY",
        deployment_pct=Decimal("0.05"),
        deployment_amount=Decimal("5000"),
    )

    crash_decision = DeploymentDecision(
        action="DEPLOY",
        deployment_pct=Decimal("0.08"),
        deployment_amount=Decimal("8000"),
    )

    regime_deployment_engine.evaluate.return_value = regime_decision
    crash_deployment_engine.evaluate.return_value = crash_decision

    service = DeploymentOrchestrationService(
        portfolio_service=portfolio_service,
        regime_engine=regime_engine,
        crash_manager=crash_manager,
        regime_deployment_engine=regime_deployment_engine,
        crash_deployment_engine=crash_deployment_engine,
    )

    result = service.evaluate(
        snapshot_id=456,
        market_data={"test": "data"},
    )

    assert result is crash_decision
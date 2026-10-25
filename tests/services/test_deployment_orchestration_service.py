
import pytest
from decimal import Decimal
from unittest.mock import MagicMock
from datetime import date
from models.account import Account
from models.snapshot import Snapshot

from models.deployment_evaluation import DeploymentEvaluation
from services.deployment_orchestration_service import (
    DeploymentOrchestrationService,
)
from models.account_config import (
    AccountConfig,
    AccountSettings,
    PositionLimits,
)

@pytest.fixture
def account():
    return AccountConfig(
        name="rollover_ira",
        display_name="Rollover IRA",
        account_type="rollover_ira",
        risk_profile="conservative",
        account_number="test",
        institution="Fidelity",
        bucket_mapping={},
        bucket_weights={},
        tolerance=0.05,
		bucket_tolerance=0.02,
        security_targets={},
        position_limits=PositionLimits(
            max_position_pct=0.10,
            overrides={},
        ),
        settings=AccountSettings(
            rebalance_frequency="monthly",
            allow_fractional_shares=True,
            enable_recovery_trims=True,
            enable_dynamic_deployment=True,
        ),
    )

@pytest.fixture
def account_repository():
    repository = MagicMock()
    repository.get_by_name.return_value = Account(
        id=1,
        account_number="test",
        name="rollover_ira",
        institution="Fidelity",
    )
    return repository


@pytest.fixture
def snapshot_repository():
    repository = MagicMock()
    repository.get_latest_by_account.return_value = Snapshot(
        id=456,
        account_id=1,
        snapshot_date=date.today(),
    )
    return repository


def test_evaluate_returns_deployment_evaluation(
    account,
    account_repository,
    snapshot_repository,
):
    portfolio_service = MagicMock()
    regime_engine = MagicMock()
    regime_deployment_engine = MagicMock()
    crash_manager = MagicMock()
    crash_deployment_engine = MagicMock()
    allocation_engine = MagicMock()
    

    portfolio_service.get_bucket_allocation.return_value = {
        "defensive": MagicMock(
            market_value=Decimal("100000"),
            target_weight=Decimal("0"),
            drift_value=Decimal("100000"),
        )
    }
    portfolio_service.get_portfolio_value.return_value = Decimal("1000000")
		
    regime_engine.evaluate.return_value = {
        "regime": "RISK_ON",
        "signals": {},
    }

    expected_decision = DeploymentEvaluation(
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
        account=account,
        allocation_engine=allocation_engine,
        account_repository=account_repository,
        snapshot_repository=snapshot_repository,
    )

    

    result = service.evaluate(
        snapshot_id=123,
        market_data={"test": "data"},
    )

    assert result is expected_decision



def test_evaluate_gets_available_capital_from_portfolio_service(
    account,
    account_repository,
    snapshot_repository,
):
    portfolio_service = MagicMock()
    regime_engine = MagicMock()
    regime_deployment_engine = MagicMock()
    crash_manager = MagicMock()
    crash_deployment_engine = MagicMock()
    allocation_engine = MagicMock()

    portfolio_service.get_bucket_allocation.return_value = {
        "defensive": MagicMock(
            market_value=Decimal("175000"),
            target_weight=Decimal("0.10"),
            drift_value=Decimal("75000"),
        )
    }
    portfolio_service.get_portfolio_value.return_value = Decimal("1000000")

    regime_engine.evaluate.return_value = {
        "regime": "RISK_ON",
        "signals": {},
    }

    expected_decision = DeploymentEvaluation(
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
        account=account,
        allocation_engine=allocation_engine,
        account_repository=account_repository,
        snapshot_repository=snapshot_repository,
    )

    service.evaluate(
        snapshot_id=456,
        market_data={"test": "data"},
    )

    portfolio_service.get_bucket_allocation.assert_called_once_with(456)

def test_evaluate_uses_defensive_bucket_surplus_as_available_capital(
    account, 
    account_repository,
    snapshot_repository,):

    portfolio_service = MagicMock()
    regime_engine = MagicMock()
    regime_deployment_engine = MagicMock()
    crash_manager = MagicMock()
    crash_deployment_engine = MagicMock()
    allocation_engine = MagicMock()

    portfolio_service.get_bucket_allocation.return_value = {
        "defensive": MagicMock(
            market_value=Decimal("250000"),
            target_weight=Decimal("0.15"),
            drift_value=Decimal("100000"),
        )
    }

    portfolio_service.get_portfolio_value.return_value = Decimal("1000000")

    regime_engine.evaluate.return_value = {
        "regime": "RISK_ON",
        "signals": {},
    }

    expected_decision = DeploymentEvaluation(
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
        account=account,
        allocation_engine=allocation_engine,
        account_repository=account_repository,
        snapshot_repository=snapshot_repository,
    )

    result = service.evaluate(
        snapshot_id=456,
        market_data={"test": "data"},
    )

    assert result is expected_decision

    portfolio_service.get_bucket_allocation.assert_called_once_with(
        456
    )

    regime_deployment_engine.evaluate.assert_called_once_with(
        {
            "regime": "RISK_ON",
            "signals": {},
        },
        Decimal("100000"),
    )


def test_evaluate_does_not_deploy_negative_defensive_surplus(
    account,
    account_repository,
    snapshot_repository,
):
    portfolio_service = MagicMock()
    regime_engine = MagicMock()
    regime_deployment_engine = MagicMock()
    crash_manager = MagicMock()
    crash_deployment_engine = MagicMock()
    allocation_engine = MagicMock()

    portfolio_service.get_bucket_allocation.return_value = {
        "defensive": MagicMock(
            market_value=Decimal("100000"),
            target_weight=Decimal("0.15"),
            drift_value=Decimal("-50000"),
        )
    }

    regime_engine.evaluate.return_value = {
        "regime": "RISK_ON",
        "signals": {},
    }

    expected_decision = DeploymentEvaluation(
        action="HOLD",
        deployment_pct=Decimal("0"),
        deployment_amount=Decimal("0"),
    )

    regime_deployment_engine.evaluate.return_value = expected_decision

    service = DeploymentOrchestrationService(
        portfolio_service=portfolio_service,
        regime_engine=regime_engine,
        crash_manager=crash_manager,
        regime_deployment_engine=regime_deployment_engine,
        crash_deployment_engine=crash_deployment_engine,
        account=account,
        allocation_engine=allocation_engine,
        account_repository=account_repository,
        snapshot_repository=snapshot_repository,
    )

    result = service.evaluate(
        snapshot_id=456,
        market_data={"test": "data"},
    )

    assert result is expected_decision

    regime_deployment_engine.evaluate.assert_called_once_with(
        {
            "regime": "RISK_ON",
            "signals": {},
        },
        Decimal("0"),
    )

def test_evaluate_uses_zero_capital_when_defensive_bucket_is_missing(
    account,
    account_repository,
    snapshot_repository,
):
    portfolio_service = MagicMock()
    regime_engine = MagicMock()
    regime_deployment_engine = MagicMock()
    crash_manager = MagicMock()
    crash_deployment_engine = MagicMock()
    allocation_engine = MagicMock()

    portfolio_service.get_bucket_allocation.return_value = {}

    regime_engine.evaluate.return_value = {
        "regime": "RISK_ON",
        "signals": {},
    }

    expected_decision = DeploymentEvaluation(
        action="HOLD",
        deployment_pct=Decimal("0"),
        deployment_amount=Decimal("0"),
    )

    regime_deployment_engine.evaluate.return_value = expected_decision

    service = DeploymentOrchestrationService(
        portfolio_service=portfolio_service,
        regime_engine=regime_engine,
        crash_manager=crash_manager,
        regime_deployment_engine=regime_deployment_engine,
        crash_deployment_engine=crash_deployment_engine,
        account=account,
        allocation_engine=allocation_engine,
        account_repository=account_repository,
        snapshot_repository=snapshot_repository,
    )

    result = service.evaluate(
        snapshot_id=456,
        market_data={"test": "data"},
    )

    assert result is expected_decision

    regime_deployment_engine.evaluate.assert_called_once_with(
        {
            "regime": "RISK_ON",
            "signals": {},
        },
        Decimal("0"),
    )

def test_evaluate_passes_defensive_surplus_to_deployment_engine(
    account,
    account_repository,
    snapshot_repository,
):
    portfolio_service = MagicMock()
    regime_engine = MagicMock()
    regime_deployment_engine = MagicMock()
    crash_manager = MagicMock()
    crash_deployment_engine = MagicMock()
    allocation_engine = MagicMock()

    portfolio_service.get_bucket_allocation.return_value = {
        "defensive": MagicMock(
            market_value=Decimal("225000"),
            target_weight=Decimal("0.15"),
            drift_value=Decimal("75000"),
        )
    }
	
    portfolio_service.get_portfolio_value.return_value = Decimal("1000000")

    regime_engine.evaluate.return_value = {
        "regime": "RISK_ON",
        "signals": {},
    }

    expected_decision = DeploymentEvaluation(
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
        account=account,
        allocation_engine=allocation_engine,
        account_repository=account_repository,
        snapshot_repository=snapshot_repository,
    )

    result = service.evaluate(
        snapshot_id=456,
        market_data={"test": "data"},
    )

    assert result is expected_decision

    regime_deployment_engine.evaluate.assert_called_once_with(
        {
            "regime": "RISK_ON",
            "signals": {},
        },
        Decimal("75000"),
    )

def test_evaluate_passes_defensive_surplus_for_partial_regime_deployment(
    account,
    account_repository,
    snapshot_repository,
):
    portfolio_service = MagicMock()
    regime_engine = MagicMock()
    regime_deployment_engine = MagicMock()
    crash_manager = MagicMock()
    crash_deployment_engine = MagicMock()
    allocation_engine = MagicMock()

    portfolio_service.get_bucket_allocation.return_value = {
        "defensive": MagicMock(
            market_value=Decimal("250000"),
            target_weight=Decimal("0.15"),
            drift_value=Decimal("100000"),
        )
    }
	
    portfolio_service.get_portfolio_value.return_value = Decimal("1000000")

    regime_engine.evaluate.return_value = {
        "regime": "RISK_ON",
        "signals": {},
    }

    expected_decision = DeploymentEvaluation(
        action="DEPLOY",
        deployment_pct=Decimal("0.50"),
        deployment_amount=Decimal("50000"),
    )

    regime_deployment_engine.evaluate.return_value = expected_decision

    service = DeploymentOrchestrationService(
        portfolio_service=portfolio_service,
        regime_engine=regime_engine,
        crash_manager=crash_manager,
        regime_deployment_engine=regime_deployment_engine,
        crash_deployment_engine=crash_deployment_engine,
        account=account,
        allocation_engine=allocation_engine,
        account_repository=account_repository,
        snapshot_repository=snapshot_repository,
    )

    result = service.evaluate(
        snapshot_id=456,
        market_data={"test": "data"},
    )

    assert result is expected_decision

    regime_deployment_engine.evaluate.assert_called_once_with(
        {
            "regime": "RISK_ON",
            "signals": {},
        },
        Decimal("100000"),
    )

def test_evaluate_passes_market_data_to_regime_engine(
    account,
    account_repository,
    snapshot_repository,
):
    portfolio_service = MagicMock()
    regime_engine = MagicMock()
    regime_deployment_engine = MagicMock()
    crash_manager = MagicMock()
    crash_deployment_engine = MagicMock()
    allocation_engine = MagicMock()

    portfolio_service.get_bucket_allocation.return_value = {
        "defensive": MagicMock(
			market_value=Decimal("175000"),
			target_weight=Decimal("0.10"),
			drift_value=Decimal("75000"),
		)
	}
    portfolio_service.get_portfolio_value.return_value = Decimal("1000000")

    market_data = {
        "sp500": 6500,
        "vix": 15,
    }

    regime_result = {
        "regime": "RISK_ON",
        "signals": {},
    }

    regime_engine.evaluate.return_value = regime_result

    regime_deployment_engine.evaluate.return_value = DeploymentEvaluation(
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
        account=account,
        allocation_engine=allocation_engine,
        account_repository=account_repository,
        snapshot_repository=snapshot_repository,
    )

    service.evaluate(
        snapshot_id=456,
        market_data=market_data,
    )

    regime_engine.evaluate.assert_called_once_with(market_data)

def test_evaluate_passes_regime_and_capital_to_regime_deployment_engine(
    account,
    account_repository,
    snapshot_repository,
):

    portfolio_service = MagicMock()
    regime_engine = MagicMock()
    crash_manager = MagicMock()
    regime_deployment_engine = MagicMock()
    crash_deployment_engine = MagicMock()
    allocation_engine = MagicMock()

    available_capital = Decimal("75000")

    regime_result = {
        "regime": "RISK_ON",
        "signals": {},
    }

    portfolio_service.get_bucket_allocation.return_value = {
        "defensive": MagicMock(
            market_value=Decimal("175000"),
            target_weight=Decimal("0.10"),
            drift_value=available_capital,
        )
    }
    portfolio_service.get_portfolio_value.return_value = Decimal("1000000")
    regime_engine.evaluate.return_value = regime_result

    expected_decision = DeploymentEvaluation(
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
        account=account,
        allocation_engine=allocation_engine,
        account_repository=account_repository,
        snapshot_repository=snapshot_repository,
    )

    service.evaluate(
        snapshot_id=456,
        market_data={"test": "data"},
    )

    regime_deployment_engine.evaluate.assert_called_once_with(
        regime_result,
        available_capital,
    )

def test_evaluate_rejects_invalid_snapshot_id(
    account,
    account_repository,
    snapshot_repository,
):
    portfolio_service = MagicMock()
    regime_engine = MagicMock()
    regime_deployment_engine = MagicMock()
    crash_manager = MagicMock()
    crash_deployment_engine = MagicMock()
    allocation_engine = MagicMock()

    service = DeploymentOrchestrationService(
        portfolio_service=portfolio_service,
        regime_engine=regime_engine,
        crash_manager=crash_manager,
        regime_deployment_engine=regime_deployment_engine,
        crash_deployment_engine=crash_deployment_engine,
        account=account,
        allocation_engine=allocation_engine,
        account_repository=account_repository,
        snapshot_repository=snapshot_repository,
    )

    for invalid_id in (0, -1, True, False, "123"):
        with pytest.raises(ValueError, match="Snapshot ID"):
            service.evaluate(
                snapshot_id=invalid_id,
                market_data={"test": "data"},
            )

def test_crash_deployment_takes_priority_over_regime_deployment(
    account,
    account_repository,
    snapshot_repository,
):
    portfolio_service = MagicMock()
    regime_engine = MagicMock()
    crash_manager = MagicMock()
    regime_deployment_engine = MagicMock()
    crash_deployment_engine = MagicMock()
    allocation_engine = MagicMock()

    available_capital = Decimal("100000")

    portfolio_service.get_bucket_allocation.return_value = {
        "defensive": MagicMock(
			market_value=available_capital,
			target_weight=Decimal("0"),
			drift_value=available_capital,
		)
	}
    portfolio_service.get_portfolio_value.return_value = Decimal("1000000")

    regime_engine.evaluate.return_value = {
        "regime": "RISK_ON",
        "signals": {},
    }

    crash_manager.run.return_value = {
        "close": 4000,
        "cycle_peak": 5000,
        "drawdown": -0.20,
    }

    regime_decision = DeploymentEvaluation(
        action="DEPLOY",
        deployment_pct=Decimal("0.05"),
        deployment_amount=Decimal("5000"),
    )

    crash_decision = DeploymentEvaluation(
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
        account=account,
        allocation_engine=allocation_engine,
        account_repository=account_repository,
        snapshot_repository=snapshot_repository,
    )

    result = service.evaluate(
        snapshot_id=456,
        market_data={"test": "data"},
    )

    assert result is crash_decision

def test_evaluate_uses_real_regime_engine(
    account,
    account_repository,
    snapshot_repository,
):
    from engine.regime.regime_engine import RegimeEngine

    portfolio_service = MagicMock()
    regime_deployment_engine = MagicMock()
    crash_manager = MagicMock()
    crash_deployment_engine = MagicMock()
    allocation_engine = MagicMock()

    portfolio_service.get_bucket_allocation.return_value = {
        "defensive": MagicMock(
            market_value=Decimal("100000"),
            target_weight=Decimal("0"),
            drift_value=Decimal("100000"),
        )
    }

    regime_config = {
        "signals": {},
        "regimes": {},
        "fallback_regime": "TRANSITION",
    }

    regime_engine = RegimeEngine(regime_config)

    expected_decision = DeploymentEvaluation(
        action="HOLD",
        deployment_pct=Decimal("0"),
        deployment_amount=Decimal("0"),
    )

    regime_deployment_engine.evaluate.return_value = expected_decision

    market_data = {
        "latest": {},
        "dma50": {},
        "dma200": {},
    }

    service = DeploymentOrchestrationService(
        portfolio_service=portfolio_service,
        regime_engine=regime_engine,
        crash_manager=crash_manager,
        regime_deployment_engine=regime_deployment_engine,
        crash_deployment_engine=crash_deployment_engine,
        account=account,
        allocation_engine=allocation_engine,
        account_repository=account_repository,
        snapshot_repository=snapshot_repository,
    )

    result = service.evaluate(
        snapshot_id=456,
        market_data=market_data,
    )

    assert result is expected_decision

    regime_deployment_engine.evaluate.assert_called_once_with(
        {
            "signals": {},
            "regime": "TRANSITION",
        },
        Decimal("100000"),
    )



def test_evaluate_holds_when_dynamic_deployment_is_disabled(
    account,
    account_repository,
    snapshot_repository,
):
    portfolio_service = MagicMock()
    regime_engine = MagicMock()
    regime_deployment_engine = MagicMock()
    crash_manager = MagicMock()
    crash_deployment_engine = MagicMock()
    allocation_engine = MagicMock()

    account = AccountConfig(
        name="rollover_ira",
        display_name="Rollover IRA",
        account_type="rollover_ira",
        risk_profile="conservative",
        account_number="test",
        institution="Fidelity",
        bucket_mapping={},
        bucket_weights={},
        tolerance=0.05,
		bucket_tolerance=0.02,
        security_targets={},
        position_limits=PositionLimits(
            max_position_pct=0.10,
            overrides={},
        ),
        settings=AccountSettings(
            rebalance_frequency="monthly",
            allow_fractional_shares=True,
            enable_recovery_trims=True,
            enable_dynamic_deployment=False,
        ),
    )

    portfolio_service.get_bucket_allocation.return_value = {
        "defensive": MagicMock(
            market_value=Decimal("250000"),
            target_weight=Decimal("0.15"),
            drift_value=Decimal("100000"),
        )
    }

    regime_engine.evaluate.return_value = {
        "regime": "RISK_ON",
        "signals": {},
    }

    crash_manager.run.return_value = {
        "drawdown": Decimal("0"),
    }

    service = DeploymentOrchestrationService(
        portfolio_service=portfolio_service,
        regime_engine=regime_engine,
        crash_manager=crash_manager,
        regime_deployment_engine=regime_deployment_engine,
        crash_deployment_engine=crash_deployment_engine,
        account=account,
        allocation_engine=allocation_engine,
        account_repository=account_repository,
        snapshot_repository=snapshot_repository,
    )

    result = service.evaluate(
        snapshot_id=456,
        market_data={"test": "data"},
    )

    assert result.action == "HOLD"
    assert result.deployment_pct == Decimal("0")
    assert result.deployment_amount == Decimal("0")

def test_crash_deployment_overrides_disabled_dynamic_deployment(
    account,
    account_repository,
    snapshot_repository,
):
    portfolio_service = MagicMock()
    regime_engine = MagicMock()
    regime_deployment_engine = MagicMock()
    crash_manager = MagicMock()
    crash_deployment_engine = MagicMock()
    allocation_engine = MagicMock()

    account = AccountConfig(
        name="rollover_ira",
        display_name="Rollover IRA",
        account_type="rollover_ira",
        risk_profile="conservative",
        account_number="test",
        institution="Fidelity",
        bucket_mapping={},
        bucket_weights={},
        tolerance=0.05,
		bucket_tolerance=0.02,
        security_targets={},
        position_limits=PositionLimits(
            max_position_pct=0.10,
            overrides={},
        ),
        settings=AccountSettings(
            rebalance_frequency="monthly",
            allow_fractional_shares=True,
            enable_recovery_trims=True,
            enable_dynamic_deployment=False,
        ),
    )

    portfolio_service.get_bucket_allocation.return_value = {
        "defensive": MagicMock(
            market_value=Decimal("250000"),
            target_weight=Decimal("0.15"),
            drift_value=Decimal("100000"),
        )
    }
	
    portfolio_service.get_portfolio_value.return_value = Decimal("1000000")

    regime_engine.evaluate.return_value = {
        "regime": "RISK_ON",
        "signals": {},
    }

    crash_manager.run.return_value = {
        "drawdown": Decimal("-0.20"),
    }

    crash_deployment_engine.evaluate.return_value = DeploymentEvaluation(
        action="DEPLOY",
        deployment_pct=Decimal("0.05"),
        deployment_amount=Decimal("5000"),
    )

    service = DeploymentOrchestrationService(
        portfolio_service=portfolio_service,
        regime_engine=regime_engine,
        crash_manager=crash_manager,
        regime_deployment_engine=regime_deployment_engine,
        crash_deployment_engine=crash_deployment_engine,
        account=account,
        allocation_engine=allocation_engine,
        account_repository=account_repository,
        snapshot_repository=snapshot_repository,
    )

    result = service.evaluate(
        snapshot_id=456,
        market_data={"test": "data"},
    )

    assert result.action == "DEPLOY"
    assert result.deployment_pct == Decimal("0.05")
    assert result.deployment_amount == Decimal("5000")

# Test proving that the orchestration layer passes the correct drawdown and available capital to the crash engine.
def test_evaluate_passes_crash_drawdown_and_capital_to_crash_engine(
    account,
    account_repository,
    snapshot_repository,
):
    portfolio_service = MagicMock()
    regime_engine = MagicMock()
    regime_deployment_engine = MagicMock()
    crash_manager = MagicMock()
    crash_deployment_engine = MagicMock()
    allocation_engine = MagicMock()

    available_capital = Decimal("75000")

    portfolio_service.get_bucket_allocation.return_value = {
        "defensive": MagicMock(
            market_value=Decimal("175000"),
            target_weight=Decimal("0.15"),
            drift_value=available_capital,
        )
    }
	
    portfolio_service.get_portfolio_value.return_value = Decimal("1000000")

    regime_engine.evaluate.return_value = {
        "regime": "RISK_ON",
        "signals": {},
    }

    regime_deployment_engine.evaluate.return_value = DeploymentEvaluation(
        action="HOLD",
        deployment_pct=Decimal("0"),
        deployment_amount=Decimal("0"),
    )

    crash_manager.run.return_value = {
        "drawdown": Decimal("-0.20"),
    }

    crash_deployment_engine.evaluate.return_value = DeploymentEvaluation(
        action="DEPLOY",
        deployment_pct=Decimal("0.05"),
        deployment_amount=Decimal("3750"),
    )

    service = DeploymentOrchestrationService(
        portfolio_service=portfolio_service,
        regime_engine=regime_engine,
        crash_manager=crash_manager,
        regime_deployment_engine=regime_deployment_engine,
        crash_deployment_engine=crash_deployment_engine,
        account=account,
        allocation_engine=allocation_engine,
        account_repository=account_repository,
        snapshot_repository=snapshot_repository,
    )

    service.evaluate(
        snapshot_id=456,
        market_data={"test": "data"},
    )

    crash_deployment_engine.evaluate.assert_called_once_with(
        Decimal("-0.20"),
        available_capital,
    )

def test_allocate_deployment_passes_portfolio_data_to_allocation_engine(
    account,
    account_repository,
    snapshot_repository,
):
    portfolio_service = MagicMock()
    regime_engine = MagicMock()
    regime_deployment_engine = MagicMock()
    crash_manager = MagicMock()
    crash_deployment_engine = MagicMock()
    allocation_engine = MagicMock()

    actual_targets = {
        "FTEC": Decimal("0.05"),
        "SOXX": Decimal("0.02"),
    }

    portfolio_value = Decimal("1000000")
    deployment_amount = Decimal("20000")

    portfolio_service.calculate_position_portfolio_weights.return_value = (
        actual_targets
    )
    portfolio_service.get_portfolio_value.return_value = portfolio_value

    allocation_engine.allocate_deployment.return_value = {
        "FTEC": Decimal("10000"),
        "SOXX": Decimal("10000"),
    }

    account.security_targets = {
        "FTEC": 0.07,
        "SOXX": 0.04,
    }

    account.bucket_mapping = {
        "FTEC": "equity_growth",
        "SOXX": "equity_growth",
    }

    service = DeploymentOrchestrationService(
        portfolio_service=portfolio_service,
        regime_engine=regime_engine,
        crash_manager=crash_manager,
        regime_deployment_engine=regime_deployment_engine,
        crash_deployment_engine=crash_deployment_engine,
        account=account,
        allocation_engine=allocation_engine,
        account_repository=account_repository,
        snapshot_repository=snapshot_repository,
    )

    result = service.allocate_deployment(
        snapshot_id=456,
        deployment_amount=deployment_amount,
    )

    assert result == {
        "FTEC": Decimal("10000"),
        "SOXX": Decimal("10000"),
    }

    portfolio_service.calculate_position_portfolio_weights.assert_called_once_with(
        456
    )

    portfolio_service.get_portfolio_value.assert_called_once_with(
        456
    )

    allocation_engine.allocate_deployment.assert_called_once_with(
        deployment_amount=deployment_amount,
        actual_targets=actual_targets,
        desired_targets={
            "FTEC": Decimal("0.07"),
            "SOXX": Decimal("0.04"),
        },
        portfolio_value=portfolio_value,
        eligible_securities=["FTEC", "SOXX"],
    )


def test_evaluate_uses_latest_snapshot_from_today(
    account,
    account_repository,
    snapshot_repository,
):
    from datetime import date
    from models.snapshot import Snapshot

    portfolio_service = MagicMock()
    regime_engine = MagicMock()
    regime_deployment_engine = MagicMock()
    crash_manager = MagicMock()
    crash_deployment_engine = MagicMock()
    allocation_engine = MagicMock()

    latest_snapshot = Snapshot(
        id=456,
        account_id=1,
        snapshot_date=date.today(),
    )

    account_repository.get_by_name.return_value = Account(
        id=1,
        account_number="test",
        name="rollover_ira",
        institution="Fidelity",
    )
    snapshot_repository.get_latest_by_account.return_value = (
        latest_snapshot
    )

    portfolio_service.get_bucket_allocation.return_value = {
        "defensive": MagicMock(
            market_value=Decimal("100000"),
            target_weight=Decimal("0"),
            drift_value=Decimal("100000"),
        )
    }

    regime_engine.evaluate.return_value = {
        "regime": "RISK_ON",
        "signals": {},
    }
    regime_deployment_engine.evaluate.return_value = (
        DeploymentEvaluation(
            action="HOLD",
            deployment_pct=Decimal("0"),
            deployment_amount=Decimal("0"),
        )
    )
    crash_manager.run.return_value = {
        "drawdown": Decimal("0"),
    }
    crash_deployment_engine.evaluate.return_value = (
        DeploymentEvaluation(
            action="HOLD",
            deployment_pct=Decimal("0"),
            deployment_amount=Decimal("0"),
        )
    )

    service = DeploymentOrchestrationService(
        portfolio_service=portfolio_service,
        regime_engine=regime_engine,
        crash_manager=crash_manager,
        regime_deployment_engine=regime_deployment_engine,
        crash_deployment_engine=crash_deployment_engine,
        account=account,
        allocation_engine=allocation_engine,
        account_repository=account_repository,
        snapshot_repository=snapshot_repository,
    )

    service.evaluate(
        snapshot_id=123,
        market_data={"test": "data"},
    )

    portfolio_service.get_bucket_allocation.assert_called_once_with(
        456
    )


def test_evaluate_rejects_stale_snapshot(
    account,
    account_repository,
    snapshot_repository,
):
    from datetime import date, timedelta
    from models.snapshot import Snapshot

    portfolio_service = MagicMock()
    regime_engine = MagicMock()
    crash_manager = MagicMock()
    regime_deployment_engine = MagicMock()
    crash_deployment_engine = MagicMock()
    allocation_engine = MagicMock()

    account_repository.get_by_name.return_value = Account(
        id=1,
        account_number="test",
        name="rollover_ira",
        institution="Fidelity",
    )
    snapshot_repository.get_latest_by_account.return_value = Snapshot(
        id=456,
        account_id=1,
        snapshot_date=date.today() - timedelta(days=1),
    )

    service = DeploymentOrchestrationService(
        portfolio_service=portfolio_service,
        regime_engine=regime_engine,
        crash_manager=crash_manager,
        regime_deployment_engine=regime_deployment_engine,
        crash_deployment_engine=crash_deployment_engine,
        account=account,
        allocation_engine=allocation_engine,
        account_repository=account_repository,
        snapshot_repository=snapshot_repository,
    )

    with pytest.raises(
        ValueError,
        match="not from today",
    ):
        service.evaluate(
            snapshot_id=123,
            market_data={"test": "data"},
        )

    portfolio_service.get_bucket_allocation.assert_not_called()
    regime_engine.evaluate.assert_not_called()
    crash_manager.run.assert_not_called()


def test_evaluate_rejects_missing_snapshot(
    account,
    account_repository,
    snapshot_repository,
):
    portfolio_service = MagicMock()
    regime_engine = MagicMock()
    crash_manager = MagicMock()
    regime_deployment_engine = MagicMock()
    crash_deployment_engine = MagicMock()
    allocation_engine = MagicMock()

    account_repository.get_by_name.return_value = Account(
        id=1,
        account_number="test",
        name="rollover_ira",
        institution="Fidelity",
    )
    snapshot_repository.get_latest_by_account.return_value = None

    service = DeploymentOrchestrationService(
        portfolio_service=portfolio_service,
        regime_engine=regime_engine,
        crash_manager=crash_manager,
        regime_deployment_engine=regime_deployment_engine,
        crash_deployment_engine=crash_deployment_engine,
        account=account,
        allocation_engine=allocation_engine,
        account_repository=account_repository,
        snapshot_repository=snapshot_repository,
    )

    with pytest.raises(
        ValueError,
        match="No portfolio snapshot found",
    ):
        service.evaluate(
            snapshot_id=123,
            market_data={"test": "data"},
        )

    portfolio_service.get_bucket_allocation.assert_not_called()
    regime_engine.evaluate.assert_not_called()
    crash_manager.run.assert_not_called()


def test_evaluate_blocks_deployment_when_snapshot_lookup_fails(
    account,
    account_repository,
    snapshot_repository,
):
    portfolio_service = MagicMock()
    regime_engine = MagicMock()
    crash_manager = MagicMock()
    regime_deployment_engine = MagicMock()
    crash_deployment_engine = MagicMock()
    allocation_engine = MagicMock()

    account_repository.get_by_name.return_value = Account(
        id=1,
        account_number="test",
        name="rollover_ira",
        institution="Fidelity",
    )
    snapshot_repository.get_latest_by_account.side_effect = RuntimeError(
        "Database unavailable"
    )

    service = DeploymentOrchestrationService(
        portfolio_service=portfolio_service,
        regime_engine=regime_engine,
        crash_manager=crash_manager,
        regime_deployment_engine=regime_deployment_engine,
        crash_deployment_engine=crash_deployment_engine,
        account=account,
        allocation_engine=allocation_engine,
        account_repository=account_repository,
        snapshot_repository=snapshot_repository,
    )

    with pytest.raises(
        ValueError,
        match="Unable to verify the latest portfolio snapshot",
    ):
        service.evaluate(
            snapshot_id=123,
            market_data={"test": "data"},
        )

    portfolio_service.get_bucket_allocation.assert_not_called()
    regime_engine.evaluate.assert_not_called()
    crash_manager.run.assert_not_called()





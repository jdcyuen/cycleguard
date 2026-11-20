from unittest.mock import Mock

import pytest

from models.account import Account
from models.account_config import (
    AccountConfig,
    AccountSettings,
    PositionLimits,
)
from models.account_match import AccountMatch
from models.account_reconciliation_result import AccountReconciliationResult
from services.account_reconciliation_orchestration_service import (
    AccountReconciliationOrchestrationService,
	AccountReconciliationOrchestrationError,
    AccountRegistrationApprovalError,
    AccountRegistrationEligibilityError,
    AccountRegistrationVerificationError,
)
from services.account_registration_service import AccountRegistrationError


@pytest.fixture
def reconciliation_service():
    return Mock()


@pytest.fixture
def registration_service():
    return Mock()


@pytest.fixture
def service(reconciliation_service, registration_service):
    return AccountReconciliationOrchestrationService(
        account_repo=Mock(),
        reconciliation_service=reconciliation_service,
        registration_service=registration_service,
    )


def make_config(account_number="Z32228042"):
    return AccountConfig(
        name="joint_wros",
        display_name="Joint WROS TOD",
        account_type="taxable",
        risk_profile="moderate",
        account_number=account_number,
        institution="Fidelity",
        bucket_mapping={},
        bucket_weights={},
        tolerance=0.05,
        bucket_tolerance=0.05,
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


def make_account(account_number="Z32228042"):
    return Account(
        id=123,
        account_number=account_number,
        name="Joint WROS TOD",
        institution="Fidelity",
    )


# ---------------------------------------------------------
# Successful registration and verification
# ---------------------------------------------------------

def test_register_pending_account_with_approval(
    service,
    reconciliation_service,
    registration_service,
):
    config = make_config()
    account = make_account()

    reconciliation_service.reconcile.side_effect = [
        AccountReconciliationResult(
            pending_registration=[config],
        ),
        AccountReconciliationResult(
            active_accounts=[
                AccountMatch(
                    database_account=account,
                    account_config=config,
                )
            ],
        ),
    ]
    registration_service.register.return_value = account

    confirmation = Mock(return_value=True)

    result = service.register_pending_account(
        "Z32228042",
        confirmation,
    )

    assert result is account
    confirmation.assert_called_once_with(config)
    registration_service.register.assert_called_once_with(config)
    assert reconciliation_service.reconcile.call_count == 2


# ---------------------------------------------------------
# Explicit approval is required
# ---------------------------------------------------------

def test_declined_approval_does_not_register(
    service,
    reconciliation_service,
    registration_service,
):
    config = make_config()
    reconciliation_service.reconcile.return_value = (
        AccountReconciliationResult(
            pending_registration=[config],
        )
    )

    confirmation = Mock(return_value=False)

    result = service.register_pending_account(
        "Z32228042",
        confirmation,
    )

    assert result is None
    confirmation.assert_called_once_with(config)
    registration_service.register.assert_not_called()
    assert reconciliation_service.reconcile.call_count == 1


def test_duplicate_configurations_block_registration(
    service,
    reconciliation_service,
    registration_service,
):
    reconciliation_service.reconcile.return_value = (
        AccountReconciliationResult(
            duplicate_accounts=[Mock()],
        )
    )

    confirmation = Mock(return_value=True)

    with pytest.raises(AccountReconciliationOrchestrationError):
        service.register_pending_account(
            "Z32228042",
            confirmation,
        )

    confirmation.assert_not_called()
    registration_service.register.assert_not_called()


def test_missing_pending_configuration_blocks_registration(
    service,
    reconciliation_service,
    registration_service,
):
    reconciliation_service.reconcile.return_value = (
        AccountReconciliationResult()
    )

    confirmation = Mock(return_value=True)

    with pytest.raises(AccountRegistrationEligibilityError):
        service.register_pending_account(
            "Z32228042",
            confirmation,
        )

    confirmation.assert_not_called()
    registration_service.register.assert_not_called()


# ---------------------------------------------------------
# Approval callback validation
# ---------------------------------------------------------

def test_confirmation_callback_failure_is_wrapped(
    service,
    reconciliation_service,
    registration_service,
):
    config = make_config()
    reconciliation_service.reconcile.return_value = (
        AccountReconciliationResult(
            pending_registration=[config],
        )
    )

    def failing_confirmation(_config):
        raise RuntimeError("Prompt failed")

    with pytest.raises(AccountRegistrationApprovalError):
        service.register_pending_account(
            "Z32228042",
            failing_confirmation,
        )

    registration_service.register.assert_not_called()


def test_confirmation_callback_must_return_boolean(
    service,
    reconciliation_service,
    registration_service,
):
    config = make_config()
    reconciliation_service.reconcile.return_value = (
        AccountReconciliationResult(
            pending_registration=[config],
        )
    )

    confirmation = Mock(return_value="yes")

    with pytest.raises(AccountRegistrationApprovalError):
        service.register_pending_account(
            "Z32228042",
            confirmation,
        )

    registration_service.register.assert_not_called()


# ---------------------------------------------------------
# Registration and post-registration verification
# ---------------------------------------------------------

def test_registration_failure_is_propagated(
    service,
    reconciliation_service,
    registration_service,
):
    config = make_config()
    reconciliation_service.reconcile.return_value = (
        AccountReconciliationResult(
            pending_registration=[config],
        )
    )
    registration_service.register.side_effect = (
        AccountRegistrationError("Database registration failed")
    )

    with pytest.raises(AccountRegistrationError):
        service.register_pending_account(
            "Z32228042",
            Mock(return_value=True),
        )

    assert reconciliation_service.reconcile.call_count == 1


def test_registration_requires_post_registration_verification(
    service,
    reconciliation_service,
    registration_service,
):
    config = make_config()
    account = make_account()

    reconciliation_service.reconcile.side_effect = [
        AccountReconciliationResult(
            pending_registration=[config],
        ),
        AccountReconciliationResult(),
    ]
    registration_service.register.return_value = account

    with pytest.raises(AccountRegistrationVerificationError):
        service.register_pending_account(
            "Z32228042",
            Mock(return_value=True),
        )

    assert reconciliation_service.reconcile.call_count == 2

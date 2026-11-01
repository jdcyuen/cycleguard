from datetime import date, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from services.drift_detection_orchestration_service import (
    DriftDetectionOrchestrationService,
    get_snapshot_date,
    normalize_account_number,
)


@pytest.fixture
def dependencies():
    db_connection = MagicMock()
    account_repository = MagicMock()
    snapshot_repository = MagicMock()
    config_loader = MagicMock()

    service = DriftDetectionOrchestrationService(
        db_connection=db_connection,
        account_repository=account_repository,
        snapshot_repository=snapshot_repository,
        config_loader=config_loader,
    )

    return (
        service,
        db_connection,
        account_repository,
        snapshot_repository,
        config_loader,
    )


def test_normalize_account_number_preserves_existing_behavior():
    assert normalize_account_number(" 12 34 ") == "1234"
    assert normalize_account_number(None) == ""
    assert normalize_account_number("ab-12") == "ab-12"


def test_get_snapshot_date_accepts_date_and_datetime():
    snapshot_date = date(2026, 10, 27)
    snapshot_datetime = datetime(2026, 10, 27, 14, 30)

    assert get_snapshot_date(
        SimpleNamespace(snapshot_date=snapshot_date)
    ) == snapshot_date
    assert get_snapshot_date(
        SimpleNamespace(snapshot_date=snapshot_datetime)
    ) == snapshot_date
    assert get_snapshot_date(None) is None
    assert get_snapshot_date(
        SimpleNamespace(snapshot_date=None)
    ) is None


def test_list_configured_accounts_matches_normalized_numbers(dependencies):
    service, _, account_repository, _, config_loader = dependencies

    database_account = SimpleNamespace(
        id=1,
        name="Retirement Account",
        account_number=" 12 34 ",
    )
    config = SimpleNamespace(account_number="1234")

    account_repository.list_accounts.return_value = [database_account]
    config_loader.load.return_value = [config]

    result = service.list_configured_accounts()

    assert result == [(database_account, config)]


def test_list_configured_accounts_skips_unmatched_accounts(dependencies):
    service, _, account_repository, _, config_loader = dependencies

    account_repository.list_accounts.return_value = [
        SimpleNamespace(id=1, name="Unmatched", account_number="9999")
    ]
    config_loader.load.return_value = [
        SimpleNamespace(account_number="1234")
    ]

    assert service.list_configured_accounts() == []


def test_list_configured_accounts_propagates_loader_failure(dependencies):
    service, _, _, _, config_loader = dependencies
    config_loader.load.side_effect = OSError("configuration unavailable")

    with pytest.raises(OSError, match="configuration unavailable"):
        service.list_configured_accounts()


def test_evaluate_account_returns_message_when_snapshot_missing(dependencies):
    service, _, _, snapshot_repository, _ = dependencies
    account = SimpleNamespace(id=1, name="Retirement Account")
    config = SimpleNamespace()
    snapshot_repository.get_latest_by_account.return_value = None

    result = service.evaluate_account(account, config)

    assert result.database_account is account
    assert result.account_config is config
    assert result.snapshot is None
    assert result.rows == []
    assert result.message == "No stored snapshot exists for this account."


@pytest.mark.parametrize(
    "account",
    [
        None,
        SimpleNamespace(id=None, name="Invalid"),
        SimpleNamespace(id="1", name="Invalid"),
        SimpleNamespace(id=True, name="Invalid"),
    ],
)
def test_evaluate_account_rejects_invalid_database_account(
    dependencies, account
):
    service, _, _, snapshot_repository, _ = dependencies

    with pytest.raises(ValueError, match="database_account|required|integer ID"):
        service.evaluate_account(account, SimpleNamespace())

    snapshot_repository.get_latest_by_account.assert_not_called()


def test_evaluate_account_rejects_missing_configuration(dependencies):
    service, _, _, snapshot_repository, _ = dependencies

    with pytest.raises(ValueError, match="account_config is required"):
        service.evaluate_account(
            SimpleNamespace(id=1, name="Retirement Account"),
            None,
        )

    snapshot_repository.get_latest_by_account.assert_not_called()


def test_evaluate_account_propagates_snapshot_repository_failure(dependencies):
    service, _, _, snapshot_repository, _ = dependencies
    snapshot_repository.get_latest_by_account.side_effect = RuntimeError(
        "database unavailable"
    )

    with pytest.raises(RuntimeError, match="database unavailable"):
        service.evaluate_account(
            SimpleNamespace(id=1, name="Retirement Account"),
            SimpleNamespace(),
        )


def test_evaluate_account_rejects_invalid_snapshot_id(dependencies):
    service, _, _, snapshot_repository, _ = dependencies
    snapshot_repository.get_latest_by_account.return_value = (
        SimpleNamespace(id="invalid", snapshot_date=date(2026, 10, 27))
    )

    with pytest.raises(ValueError, match="snapshot must have a valid integer ID"):
        service.evaluate_account(
            SimpleNamespace(id=1, name="Retirement Account"),
            SimpleNamespace(),
        )


def test_evaluate_account_delegates_to_drift_service(dependencies):
    service, db_connection, _, snapshot_repository, _ = dependencies
    account = SimpleNamespace(id=1, name="Retirement Account")
    config = SimpleNamespace()
    snapshot = SimpleNamespace(
        id=42,
        snapshot_date=date(2026, 10, 27),
    )
    expected_rows = [{"Row Type": "Position", "Symbol": "FTEC"}]
    snapshot_repository.get_latest_by_account.return_value = snapshot

    with (
        patch(
            "services.drift_detection_orchestration_service.PositionRepository"
        ) as position_repository_class,
        patch(
            "services.drift_detection_orchestration_service."
            "PortfolioAggregationService"
        ) as portfolio_service_class,
        patch(
            "services.drift_detection_orchestration_service."
            "DriftDetectionService"
        ) as drift_service_class,
    ):
        drift_service_class.return_value.evaluate.return_value = expected_rows

        result = service.evaluate_account(account, config)

    position_repository_class.assert_called_once_with(db_connection)
    portfolio_service_class.assert_called_once_with(
        position_repository_class.return_value,
        config,
    )
    drift_service_class.assert_called_once_with(
        portfolio_service_class.return_value,
        config,
    )
    drift_service_class.return_value.evaluate.assert_called_once_with(42)

    assert result.database_account is account
    assert result.account_config is config
    assert result.snapshot is snapshot
    assert result.snapshot_date == date(2026, 10, 27)
    assert result.rows == expected_rows
    assert result.message is None


def test_evaluate_account_propagates_calculation_failure(dependencies):
    service, _, _, snapshot_repository, _ = dependencies
    snapshot_repository.get_latest_by_account.return_value = (
        SimpleNamespace(id=42, snapshot_date=date(2026, 10, 27))
    )

    with (
        patch(
            "services.drift_detection_orchestration_service.PositionRepository"
        ),
        patch(
            "services.drift_detection_orchestration_service."
            "PortfolioAggregationService"
        ),
        patch(
            "services.drift_detection_orchestration_service."
            "DriftDetectionService"
        ) as drift_service_class,
    ):
        drift_service_class.return_value.evaluate.side_effect = RuntimeError(
            "calculation failed"
        )

        with pytest.raises(RuntimeError, match="calculation failed"):
            service.evaluate_account(
                SimpleNamespace(id=1, name="Retirement Account"),
                SimpleNamespace(),
            )

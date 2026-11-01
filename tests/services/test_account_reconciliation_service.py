
import pytest
from unittest.mock import Mock

from models.account import Account
from services.account_reconciliation_service import (
    AccountReconciliationService,
    AccountReconciliationServiceError,
    normalize_account_number,
)


@pytest.fixture
def account_repo():
    return Mock()


@pytest.fixture
def loader():
    return Mock()


@pytest.fixture
def service(account_repo, loader):
    return AccountReconciliationService(
        account_repo=account_repo,
        loader=loader,
    )


def make_config(account_number, name="test_account"):
    config = Mock()
    config.account_number = account_number
    config.name = name
    config.display_name = name.replace("_", " ").title()
    config.institution = "fidelity"
    return config


def make_account(account_number, name="test_account", account_id=1):
    return Account(
        id=account_id,
        account_number=account_number,
        name=name,
        institution="fidelity",
    )


# ---------------------------------------------------------
# Normalization
# ---------------------------------------------------------

@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (" 12 345 678 ", "12345678"),
        ("ab-123", "AB-123"),
        ("AB-123", "AB-123"),
        (" Ab - 123 ", "AB-123"),
        (None, ""),
        ("   ", ""),
    ],
)
def test_normalize_account_number(value, expected):
    assert normalize_account_number(value) == expected


# ---------------------------------------------------------
# Lifecycle classifications
# ---------------------------------------------------------

def test_reconcile_classifies_active_account(service, account_repo, loader):
    config = make_config("12 345")
    database_account = make_account("12345")

    loader.load.return_value = [config]
    account_repo.list_accounts.return_value = [database_account]

    result = service.reconcile()

    assert len(result.active_accounts) == 1
    assert result.active_accounts[0].account_config is config
    assert result.active_accounts[0].database_account is database_account
    assert result.pending_registration == []
    assert result.historical_accounts == []
    assert result.duplicate_accounts == []


def test_reconcile_classifies_pending_account(service, account_repo, loader):
    config = make_config("12345")

    loader.load.return_value = [config]
    account_repo.list_accounts.return_value = []

    result = service.reconcile()

    assert result.active_accounts == []
    assert result.pending_registration == [config]
    assert result.historical_accounts == []


def test_reconcile_classifies_historical_account(service, account_repo, loader):
    database_account = make_account("12345")

    loader.load.return_value = []
    account_repo.list_accounts.return_value = [database_account]

    result = service.reconcile()

    assert result.active_accounts == []
    assert result.pending_registration == []
    assert result.historical_accounts == [database_account]


def test_reconcile_handles_empty_sources(service, account_repo, loader):
    loader.load.return_value = []
    account_repo.list_accounts.return_value = []

    result = service.reconcile()

    assert result.active_accounts == []
    assert result.pending_registration == []
    assert result.historical_accounts == []
    assert result.duplicate_accounts == []


def test_reconcile_matches_account_numbers_case_insensitively(
    service, account_repo, loader
):
    config = make_config("ab-123")
    database_account = make_account("AB-123")

    loader.load.return_value = [config]
    account_repo.list_accounts.return_value = [database_account]

    result = service.reconcile()

    assert len(result.active_accounts) == 1


# ---------------------------------------------------------
# Duplicate detection
# ---------------------------------------------------------

def test_reconcile_detects_duplicate_yaml_numbers(
    service, account_repo, loader
):
    loader.load.return_value = [
        make_config("12345", "account_one"),
        make_config("12 345", "account_two"),
    ]
    account_repo.list_accounts.return_value = []

    result = service.reconcile()

    assert result.active_accounts == []
    assert result.pending_registration == []
    assert result.duplicate_accounts
    assert result.duplicate_accounts[0].source == "YAML"
    assert result.duplicate_accounts[0].normalized_account_number == "12345"
    assert result.has_duplicates is True


def test_reconcile_detects_duplicate_database_numbers(
    service, account_repo, loader
):
    loader.load.return_value = []
    account_repo.list_accounts.return_value = [
        make_account("12345", account_id=1),
        make_account("12 345", account_id=2),
    ]

    result = service.reconcile()

    assert result.historical_accounts == []
    assert result.duplicate_accounts
    assert result.duplicate_accounts[0].source == "database"
    assert result.duplicate_accounts[0].normalized_account_number == "12345"


def test_duplicate_in_either_source_blocks_matching_in_both_sources(
    service, account_repo, loader
):
    loader.load.return_value = [
        make_config("12345"),
    ]
    account_repo.list_accounts.return_value = [
        make_account("12345", account_id=1),
        make_account("12 345", account_id=2),
    ]

    result = service.reconcile()

    assert result.active_accounts == []
    assert result.pending_registration == []
    assert result.historical_accounts == []
    assert result.has_duplicates is True


def test_reconcile_detects_case_insensitive_duplicates(
    service, account_repo, loader
):
    loader.load.return_value = [
        make_config("ab-123", "account_one"),
        make_config("AB-123", "account_two"),
    ]
    account_repo.list_accounts.return_value = []

    result = service.reconcile()

    assert result.has_duplicates is True
    assert result.duplicate_accounts[0].normalized_account_number == "AB-123"


# ---------------------------------------------------------
# Invalid account identifiers
# ---------------------------------------------------------

@pytest.mark.parametrize("invalid_number", [None, "", "   "])
def test_reconcile_rejects_missing_yaml_account_number(
    service, account_repo, loader, invalid_number
):
    loader.load.return_value = [make_config(invalid_number)]
    account_repo.list_accounts.return_value = []

    with pytest.raises(
        AccountReconciliationServiceError,
        match="missing account number",
    ):
        service.reconcile()


@pytest.mark.parametrize("invalid_number", [None, "", "   "])
def test_reconcile_rejects_missing_database_account_number(
    service, account_repo, loader, invalid_number
):
    loader.load.return_value = []
    account_repo.list_accounts.return_value = [
        make_account(invalid_number),
    ]

    with pytest.raises(
        AccountReconciliationServiceError,
        match="missing account number",
    ):
        service.reconcile()


# ---------------------------------------------------------
# Exception handling
# ---------------------------------------------------------

def test_reconcile_wraps_configuration_loading_error(
    service, loader, account_repo
):
    loader.load.side_effect = ValueError("Invalid YAML")

    with pytest.raises(
        AccountReconciliationServiceError,
        match="configuration loading failed",
    ) as exc_info:
        service.reconcile()

    assert isinstance(exc_info.value.__cause__, ValueError)
    account_repo.list_accounts.assert_not_called()


def test_reconcile_wraps_database_retrieval_error(
    service, loader, account_repo
):
    loader.load.return_value = []
    account_repo.list_accounts.side_effect = RuntimeError("Database unavailable")

    with pytest.raises(
        AccountReconciliationServiceError,
        match="Database account retrieval failed",
    ) as exc_info:
        service.reconcile()

    assert isinstance(exc_info.value.__cause__, RuntimeError)


def test_result_has_duplicates_property():
    from services.account_reconciliation_service import (
        AccountReconciliationResult,
    )

    result = AccountReconciliationResult()

    assert result.has_duplicates is False

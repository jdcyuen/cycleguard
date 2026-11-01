
import psycopg2
import pytest
from unittest.mock import Mock

from models.account import Account
from repositories.account_repo import AccountRepositoryError
from services.account_registration_service import (
    AccountRegistrationService,
    AccountRegistrationError,
    AccountRegistrationValidationError,
    AccountRegistrationConflictError,
)


@pytest.fixture
def account_repo():
    return Mock()


@pytest.fixture
def service(account_repo):
    return AccountRegistrationService(
        account_repository=account_repo,
    )


def make_config(
    account_number="Z32228042",
    display_name="Joint WROS TOD",
    institution="Fidelity",
):
    config = Mock()
    config.account_number = account_number
    config.display_name = display_name
    config.institution = institution
    return config


def make_account(
    account_number="Z32228042",
    name="Joint WROS TOD",
    account_id=123,
):
    return Account(
        id=account_id,
        account_number=account_number,
        name=name,
        institution="Fidelity",
    )


# ---------------------------------------------------------
# Successful registration
# ---------------------------------------------------------

def test_register_creates_account(service, account_repo):
    config = make_config()
    created_account = make_account()

    account_repo.get_by_account_number.return_value = None
    account_repo.create.return_value = created_account

    result = service.register(config)

    assert result is created_account

    account_repo.get_by_account_number.assert_called_once_with(
        "Z32228042"
    )

    account_repo.create.assert_called_once()

    inserted_account = account_repo.create.call_args.args[0]

    assert isinstance(inserted_account, Account)
    assert inserted_account.account_number == "Z32228042"
    assert inserted_account.name == "Joint WROS TOD"
    assert inserted_account.institution == "Fidelity"


def test_register_normalizes_account_number(service, account_repo):
    config = make_config(
        account_number=" z322 28042 "
    )

    account_repo.get_by_account_number.return_value = None
    account_repo.create.return_value = make_account()

    service.register(config)

    account_repo.get_by_account_number.assert_called_once_with(
        "Z32228042"
    )

    inserted_account = account_repo.create.call_args.args[0]

    assert inserted_account.account_number == "Z32228042"


# ---------------------------------------------------------
# Configuration validation
# ---------------------------------------------------------

@pytest.mark.parametrize(
    ("config", "expected_message"),
    [
        (None, "configuration is required"),
        (
            make_config(account_number="   "),
            "account number",
        ),
        (
            make_config(display_name="   "),
            "display name",
        ),
        (
            make_config(institution="   "),
            "institution",
        ),
    ],
)
def test_register_rejects_invalid_configuration(
    service,
    account_repo,
    config,
    expected_message,
):
    with pytest.raises(
        AccountRegistrationValidationError,
        match=expected_message,
    ):
        service.register(config)

    account_repo.get_by_account_number.assert_not_called()
    account_repo.create.assert_not_called()


# ---------------------------------------------------------
# Duplicate protection
# ---------------------------------------------------------

def test_register_rejects_existing_account(service, account_repo):
    config = make_config()

    account_repo.get_by_account_number.return_value = make_account()

    with pytest.raises(
        AccountRegistrationConflictError,
        match="already registered",
    ):
        service.register(config)

    account_repo.create.assert_not_called()

def test_register_rejects_concurrent_duplicate(
    service,
    account_repo,
):
    config = make_config()

    account_repo.get_by_account_number.return_value = None

    database_error = psycopg2.errors.UniqueViolation(
		"duplicate key value violates unique constraint"
	)

    repository_error = AccountRepositoryError(
        "Account already exists."
    )

    try:
        raise repository_error from database_error
    except AccountRepositoryError as chained_error:
        account_repo.create.side_effect = chained_error

    with pytest.raises(
        AccountRegistrationConflictError,
        match="registered by another operation",
    ):
        service.register(config)


# ---------------------------------------------------------
# Repository and unexpected failures
# ---------------------------------------------------------

def test_register_handles_lookup_failure(service, account_repo):
    config = make_config()

    account_repo.get_by_account_number.side_effect = (
        AccountRepositoryError("Database unavailable")
    )

    with pytest.raises(
        AccountRegistrationError,
        match="verify whether",
    ):
        service.register(config)

    account_repo.create.assert_not_called()


def test_register_handles_create_failure(service, account_repo):
    config = make_config()

    account_repo.get_by_account_number.return_value = None
    account_repo.create.side_effect = AccountRepositoryError(
        "Database unavailable"
    )

    with pytest.raises(
        AccountRegistrationError,
        match="Unable to register account",
    ):
        service.register(config)


def test_register_handles_unexpected_create_failure(
    service,
    account_repo,
):
    config = make_config()

    account_repo.get_by_account_number.return_value = None
    account_repo.create.side_effect = RuntimeError(
        "Unexpected failure"
    )

    with pytest.raises(
        AccountRegistrationError,
        match="Unable to register account",
    ):
        service.register(config)

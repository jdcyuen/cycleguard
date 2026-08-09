import pytest
from unittest.mock import Mock

from services.account_validation_service import (
    AccountValidationService,
    AccountValidationServiceError,
)
from models.account import Account


@pytest.fixture
def account_repo():
    return Mock()


@pytest.fixture
def loader():
    return Mock()


@pytest.fixture
def service(account_repo, loader):
    return AccountValidationService(account_repo=account_repo, loader=loader)


def test_exists_returns_true(service, account_repo):
    account_repo.get_by_name.return_value = Account(
        id=1, account_number="123", name="rollover_ira", institution="fidelity"
    )

    assert service.exists("rollover_ira") is True
    account_repo.get_by_name.assert_called_once_with("rollover_ira")


def test_exists_returns_false(service, account_repo):
    account_repo.get_by_name.return_value = None

    assert service.exists("rollover_ira") is False
    account_repo.get_by_name.assert_called_once_with("rollover_ira")


def test_add_account_success(service, account_repo, loader):
    mock_config = Mock()
    mock_config.account_number = "123456789"
    mock_config.name = "rollover_ira"
    mock_config.institution = "fidelity"
    loader.get.return_value = mock_config

    mock_created = Account(id=42, account_number="123456789", name="rollover_ira", institution="fidelity")
    account_repo.create.return_value = mock_created

    result = service.add_account("rollover_ira")

    assert result == mock_created
    loader.get.assert_called_once_with("rollover_ira")
    account_repo.create.assert_called_once_with(
        Account(account_number="123456789", name="rollover_ira", institution="fidelity")
    )


def test_add_account_missing_config(service, loader):
    loader.get.return_value = None

    with pytest.raises(ValueError, match="Unknown account 'rollover_ira'"):
        service.add_account("rollover_ira")


def test_add_account_database_error(service, account_repo, loader):
    mock_config = Mock()
    mock_config.account_number = "123456789"
    mock_config.name = "rollover_ira"
    mock_config.institution = "fidelity"
    loader.get.return_value = mock_config

    account_repo.create.side_effect = Exception("db write error")

    with pytest.raises(AccountValidationServiceError, match="Failed to add account 'rollover_ira'"):
        service.add_account("rollover_ira")
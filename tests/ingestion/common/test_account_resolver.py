from unittest.mock import MagicMock, patch
import pytest

from ingestion.common.account_resolver import AccountResolver


# ----------------------------------------------------
# Fixtures
# ----------------------------------------------------

@pytest.fixture
def resolver():
    return AccountResolver()


@pytest.fixture
def mock_account_repo():
    return MagicMock()


# ----------------------------------------------------
# get_account_names()
# ----------------------------------------------------

@patch("ingestion.common.account_resolver.get_config")
def test_get_account_names_returns_sorted_accounts(mock_get_config, resolver):

    mock_get_config.return_value = {
        "accounts": {
            "Joint": {},
            "Roth": {},
            "IRA": {},
        }
    }

    result = resolver.get_account_names()

    assert result == ["IRA", "Joint", "Roth"]


@patch("ingestion.common.account_resolver.get_config")
def test_get_account_names_empty(mock_get_config, resolver):

    mock_get_config.return_value = {
        "accounts": {}
    }

    assert resolver.get_account_names() == []


# ----------------------------------------------------
# validate_account()
# ----------------------------------------------------

@patch.object(AccountResolver, "get_account_names")
def test_validate_account_true(mock_names, resolver):

    mock_names.return_value = ["IRA", "Roth"]

    assert resolver.validate_account("IRA") is True


@patch.object(AccountResolver, "get_account_names")
def test_validate_account_false(mock_names, resolver):

    mock_names.return_value = ["IRA", "Roth"]

    assert resolver.validate_account("Joint") is False


# ----------------------------------------------------
# resolve_account()
# ----------------------------------------------------

@patch("ingestion.common.account_resolver.AccountValidationService")
def test_resolve_existing_account(
    mock_validation,
    mock_account_repo,
    resolver,
):

    validator = mock_validation.return_value
    validator.exists.return_value = True

    result = resolver.resolve_account(
        "IRA",
        mock_account_repo,
    )

    assert result == "IRA"

    validator.exists.assert_called_once_with("IRA")
    validator.add_account.assert_not_called()


@patch("ingestion.common.account_resolver.confirm_add_account")
@patch("ingestion.common.account_resolver.AccountValidationService")
def test_resolve_new_account_adds_to_database(
    mock_validation,
    mock_confirm,
    mock_account_repo,
    resolver,
):

    validator = mock_validation.return_value

    validator.exists.return_value = False
    mock_confirm.return_value = True

    result = resolver.resolve_account(
        "IRA",
        mock_account_repo,
    )

    assert result == "IRA"

    validator.add_account.assert_called_once_with("IRA")


@patch("ingestion.common.account_resolver.confirm_add_account")
@patch("ingestion.common.account_resolver.AccountValidationService")
def test_resolve_new_account_cancelled(
    mock_validation,
    mock_confirm,
    mock_account_repo,
    resolver,
):

    validator = mock_validation.return_value

    validator.exists.return_value = False
    mock_confirm.return_value = False

    with pytest.raises(SystemExit):
        resolver.resolve_account(
            "IRA",
            mock_account_repo,
        )

    validator.add_account.assert_not_called()


def test_resolve_account_no_accounts(mock_account_repo, resolver):

    mock_account_repo.list_accounts.return_value = []

    with pytest.raises(ValueError):
        resolver.resolve_account(
            None,
            mock_account_repo,
        )


@patch("builtins.input", return_value="2")
def test_resolve_account_select_existing(
    mock_input,
    mock_account_repo,
    resolver,
):

    acct1 = MagicMock()
    acct1.name = "IRA"

    acct2 = MagicMock()
    acct2.name = "Roth"

    mock_account_repo.list_accounts.return_value = [
        acct1,
        acct2,
    ]

    result = resolver.resolve_account(
        None,
        mock_account_repo,
    )

    assert result == "Roth"


@patch("builtins.input", side_effect=["abc", "3", "1"])
def test_resolve_account_invalid_then_valid(
    mock_input,
    mock_account_repo,
    resolver,
):

    acct = MagicMock()
    acct.name = "IRA"

    mock_account_repo.list_accounts.return_value = [acct]

    result = resolver.resolve_account(
        None,
        mock_account_repo,
    )

    assert result == "IRA"


# ----------------------------------------------------
# prompt_for_account()
# ----------------------------------------------------

@patch.object(AccountResolver, "get_account_names")
@patch("builtins.input", return_value="2")
def test_prompt_for_account(
    mock_input,
    mock_names,
    resolver,
):

    mock_names.return_value = [
        "IRA",
        "Roth",
    ]

    result = resolver.prompt_for_account()

    assert result == "Roth"


@patch.object(AccountResolver, "get_account_names")
def test_prompt_for_account_no_accounts(
    mock_names,
    resolver,
):

    mock_names.return_value = []

    with pytest.raises(ValueError):
        resolver.prompt_for_account()


@patch.object(AccountResolver, "get_account_names")
@patch("builtins.input", side_effect=["x", "5", "1"])
def test_prompt_for_account_retry_until_valid(
    mock_input,
    mock_names,
    resolver,
):

    mock_names.return_value = [
        "IRA",
        "Roth",
    ]

    result = resolver.prompt_for_account()

    assert result == "IRA"
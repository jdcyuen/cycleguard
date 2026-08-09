from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from ingestion.common.cli_ingestion_helper import (
    resolve_snapshot_date,
    confirm_import,
    display_results,
    confirm_add_account,
    resolve_account,
)


# ============================================================
# resolve_snapshot_date
# ============================================================

def test_resolve_snapshot_date_cli_argument():

    with patch("builtins.input", return_value="y"):

        """Test that the CLI snapshot date is used."""
        result = resolve_snapshot_date(
            "Portfolio_Positions_Jan_01_2026.csv",
            "2026-01-10",
        )

    assert result == "2026-01-10"


def test_resolve_snapshot_date_from_filename_short_month():

    result = resolve_snapshot_date(
        "Portfolio_Positions_Jan_10_2026.csv",
        None,
    )

    assert result == date(2026, 1, 10)


def test_resolve_snapshot_date_from_filename_long_month():
    result = resolve_snapshot_date(
        "Portfolio_Positions_January_10_2026.csv",
        None, 
    )

    assert result == date(2026, 1, 10)


def test_resolve_snapshot_date_fallback_today():

    """Test that today's date is used when no snapshot date is found."""
    today = date.today()

    result = resolve_snapshot_date(
        "random_file.csv",
        None,
    )

    assert result == today


# ============================================================
# confirm_import
# ============================================================

@patch("builtins.input", return_value="y")
def test_confirm_import_yes(mock_input):
    assert confirm_import("positions", "IRA") is True


@patch("builtins.input", return_value="n")
def test_confirm_import_no(mock_input):
    assert confirm_import("positions", "IRA") is False


@patch("builtins.input", return_value="Y")
def test_confirm_import_uppercase(mock_input):
    assert confirm_import("positions", "IRA") is True


# ============================================================
# display_results
# ============================================================

def test_display_results(capsys):
    result = MagicMock()

    result.import_type = "positions"
    result.account_name = "IRA"

    result.filename = "positions.csv"
    result.snapshot_date = "2025-12-31"

    result.rows_read = 45
    result.rows_imported = 42
    result.rows_skipped = 3

    result.import_history_id = 123
    result.snapshot_id = 456

    result.elapsed_ms = 125

    display_results(result)

    captured = capsys.readouterr()

    assert "Positions Import Summary" in captured.out
    assert "IRA" in captured.out
    assert "42" in captured.out
    assert "positions.csv" in captured.out
    assert "125 ms" in captured.out


# ============================================================
# confirm_add_account
# ============================================================

@patch("builtins.input", return_value="y")
def test_confirm_add_account_yes(mock_input):
    assert confirm_add_account("IRA") is True


@patch("builtins.input", return_value="n")
def test_confirm_add_account_no(mock_input):
    assert confirm_add_account("IRA") is False


@patch("builtins.input", return_value=" Y ")
def test_confirm_add_account_strip(mock_input):
    assert confirm_add_account("IRA") is True


# ============================================================
# resolve_account
# ============================================================

@patch("ingestion.common.cli_ingestion_helper.AccountValidationService")
def test_resolve_account_existing_account(mock_validation):
    repo = MagicMock()

    validation = mock_validation.return_value
    validation.exists.return_value = True

    result = resolve_account("IRA", repo)

    assert result == "IRA"

    validation.exists.assert_called_once_with("IRA")
    validation.add_account.assert_not_called()


@patch("ingestion.common.cli_ingestion_helper.confirm_add_account", return_value=True)
@patch("ingestion.common.cli_ingestion_helper.AccountValidationService")
def test_resolve_account_add_new(
    mock_validation,
    mock_confirm,
):
    repo = MagicMock()

    validation = mock_validation.return_value
    validation.exists.return_value = False

    result = resolve_account("IRA", repo)

    assert result == "IRA"

    validation.add_account.assert_called_once_with("IRA")


@patch("ingestion.common.cli_ingestion_helper.confirm_add_account", return_value=False)
@patch("ingestion.common.cli_ingestion_helper.AccountValidationService")
def test_resolve_account_decline_add(
    mock_validation,
    mock_confirm,
):
    repo = MagicMock()

    validation = mock_validation.return_value
    validation.exists.return_value = False

    with pytest.raises(SystemExit):
        resolve_account("IRA", repo)


@patch("ingestion.common.cli_ingestion_helper.AccountValidationService")
def test_resolve_account_no_accounts(mock_validation):
    repo = MagicMock()
    repo.list_accounts.return_value = []

    with pytest.raises(ValueError):
        resolve_account(None, repo)


@patch("builtins.input", return_value="2")
@patch("ingestion.common.cli_ingestion_helper.AccountValidationService")
def test_resolve_account_select_existing(
    mock_validation,
    mock_input,
):
    repo = MagicMock()

    acct1 = MagicMock()
    acct1.name = "IRA"

    acct2 = MagicMock()
    acct2.name = "Brokerage"

    repo.list_accounts.return_value = [acct1, acct2]

    result = resolve_account(None, repo)

    assert result == "Brokerage"


@patch("builtins.input", side_effect=["abc", "1"])
@patch("ingestion.common.cli_ingestion_helper.AccountValidationService")
def test_resolve_account_invalid_then_valid(
    mock_validation,
    mock_input,
    capsys,
):
    repo = MagicMock()

    acct = MagicMock()
    acct.name = "IRA"

    repo.list_accounts.return_value = [acct]

    result = resolve_account(None, repo)

    assert result == "IRA"

    captured = capsys.readouterr()

    assert "Please enter a valid number." in captured.out


@patch("builtins.input", side_effect=["5", "1"])
@patch("ingestion.common.cli_ingestion_helper.AccountValidationService")
def test_resolve_account_out_of_range_then_valid(
    mock_validation,
    mock_input,
    capsys,
):
    repo = MagicMock()

    acct = MagicMock()
    acct.name = "IRA"

    repo.list_accounts.return_value = [acct]

    result = resolve_account(None, repo)

    assert result == "IRA"

    captured = capsys.readouterr()

    assert "Selection out of range" in captured.out
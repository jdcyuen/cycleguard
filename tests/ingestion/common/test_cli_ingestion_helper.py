from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from models.account import Account
from models.account_match import AccountMatch
from models.account_reconciliation_result import (
    AccountReconciliationResult,
)

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
@patch("ingestion.common.cli_ingestion_helper.AccountReconciliationService")
def test_resolve_account_existing_account(mock_reconciliation):
    repo = MagicMock()

    account = Account(
        id=1,
        account_number="123456",
        name="IRA",
        institution="Fidelity",
    )

    account_match = AccountMatch(
        database_account=account,
        account_config=MagicMock(),
    )

    reconciliation = AccountReconciliationResult(
        active_accounts=[account_match],
    )

    mock_reconciliation.return_value.reconcile.return_value = (
        reconciliation
    )

    result = resolve_account("IRA", repo)

    assert result == "IRA"

    mock_reconciliation.return_value.reconcile.assert_called_once()


@patch("ingestion.common.cli_ingestion_helper.confirm_add_account", return_value=True)
@patch("ingestion.common.cli_ingestion_helper.AccountRegistrationService")
@patch("ingestion.common.cli_ingestion_helper.AccountReconciliationService")
def test_resolve_account_add_new(
    mock_reconciliation,
    mock_registration,
    mock_confirm,
):
    repo = MagicMock()
    pending_config = MagicMock()
    pending_config.display_name = "IRA"

    account = Account(
        id=1,
        account_number="123456",
        name="IRA",
        institution="Fidelity",
    )

    active_match = AccountMatch(
        database_account=account,
        account_config=MagicMock(),
    )

    pending_result = AccountReconciliationResult(
        pending_registration=[pending_config],
    )
    active_result = AccountReconciliationResult(
        active_accounts=[active_match],
    )

    mock_reconciliation.return_value.reconcile.side_effect = [
        pending_result,
        active_result,
    ]

    result = resolve_account("IRA", repo)

    assert result == "IRA"
    mock_confirm.assert_called_once_with("IRA")
    mock_registration.return_value.register.assert_called_once_with(
        pending_config
    )


@patch("ingestion.common.cli_ingestion_helper.confirm_add_account", return_value=False)
@patch("ingestion.common.cli_ingestion_helper.AccountRegistrationService")
@patch("ingestion.common.cli_ingestion_helper.AccountReconciliationService")
def test_resolve_account_decline_add(
    mock_reconciliation,
    mock_registration,
    mock_confirm,
):
    repo = MagicMock()
    pending_config = MagicMock()
    pending_config.display_name = "IRA"

    mock_reconciliation.return_value.reconcile.return_value = (
        AccountReconciliationResult(
            pending_registration=[pending_config],
        )
    )

    with pytest.raises(SystemExit, match="Import cancelled."):
        resolve_account("IRA", repo)

    mock_confirm.assert_called_once_with("IRA")
    mock_registration.return_value.register.assert_not_called()


@patch("ingestion.common.cli_ingestion_helper.AccountReconciliationService")
def test_resolve_account_no_accounts(mock_reconciliation):
    repo = MagicMock()

    mock_reconciliation.return_value.reconcile.return_value = (
        AccountReconciliationResult()
    )

    with pytest.raises(ValueError):
        resolve_account(None, repo)


@patch("builtins.input", return_value="2")
@patch("ingestion.common.cli_ingestion_helper.AccountReconciliationService")
def test_resolve_account_select_existing(
    mock_reconciliation,
    mock_input,
):
    repo = MagicMock()

    account1 = Account(
        id=1,
        account_number="123456",
        name="IRA",
        institution="Fidelity",
    )
    account2 = Account(
        id=2,
        account_number="789012",
        name="Brokerage",
        institution="Schwab",
    )

    mock_reconciliation.return_value.reconcile.return_value = (
        AccountReconciliationResult(
            active_accounts=[
                AccountMatch(account1, MagicMock()),
                AccountMatch(account2, MagicMock()),
            ],
        )
    )

    result = resolve_account(None, repo)

    assert result == "Brokerage"
    mock_input.assert_called_once()


@patch("builtins.input", side_effect=["abc", "1"])
@patch("ingestion.common.cli_ingestion_helper.AccountReconciliationService")
def test_resolve_account_invalid_then_valid(
    mock_reconciliation,
    mock_input,
    capsys,
):
    repo = MagicMock()

    account = Account(
        id=1,
        account_number="123456",
        name="IRA",
        institution="Fidelity",
    )

    mock_reconciliation.return_value.reconcile.return_value = (
        AccountReconciliationResult(
            active_accounts=[
                AccountMatch(account, MagicMock()),
            ],
        )
    )

    result = resolve_account(None, repo)

    assert result == "IRA"

    captured = capsys.readouterr()
    assert "Please enter a valid number." in captured.out

@patch("builtins.input", side_effect=["5", "1"])
@patch("ingestion.common.cli_ingestion_helper.AccountReconciliationService")
def test_resolve_account_out_of_range_then_valid(
    mock_reconciliation,
    mock_input,
    capsys,
):
    repo = MagicMock()

    account = Account(
        id=1,
        account_number="123456",
        name="IRA",
        institution="Fidelity",
    )

    mock_reconciliation.return_value.reconcile.return_value = (
        AccountReconciliationResult(
            active_accounts=[
                AccountMatch(account, MagicMock()),
            ],
        )
    )

    result = resolve_account(None, repo)

    assert result == "IRA"

    captured = capsys.readouterr()
    assert "Selection out of range." in captured.out

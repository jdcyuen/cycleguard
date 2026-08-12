from unittest.mock import MagicMock

import pytest

from repositories.transaction_repo import (
    TransactionRepository,
    TransactionRepositoryError,
)
from models.transaction import Transaction


@pytest.fixture
def mock_conn():
    return MagicMock()

@pytest.fixture
def mock_cursor():
    return MagicMock()



@pytest.fixture
def repository(mock_conn, mock_cursor):
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    return TransactionRepository(mock_conn)


def test_delete_by_import_history_id_returns_row_count(
    repository,
    mock_cursor,
):
    import_id = 123
    mock_cursor.rowcount = 5

    result = repository.delete_by_import_history_id(import_id)

    assert result == 5
    mock_cursor.execute.assert_called_once()


def test_delete_by_import_history_id_executes_expected_sql(
    repository,
    mock_cursor,
    mock_conn,
):
    import_history_id = 123

    repository.delete_by_import_history_id(import_history_id)

    mock_cursor.execute.assert_called_once()

    sql, params = mock_cursor.execute.call_args.args

    assert "DELETE FROM cycleguard.transactions" in sql
    assert "WHERE import_history_id = %s" in sql
    assert params == (import_history_id,)

    mock_conn.commit.assert_not_called()
    mock_conn.rollback.assert_not_called()


def test_delete_by_import_history_id_does_not_commit(
    repository,
    mock_conn,
    mock_cursor,
):
    mock_cursor.rowcount = 5

    repository.delete_by_import_history_id(123)

    mock_conn.commit.assert_not_called()
    mock_conn.rollback.assert_not_called()


def test_delete_by_import_history_id_raises_repository_error(
    repository,
    mock_cursor,
    mock_conn,
):

    mock_cursor.execute.side_effect = Exception(
        "database error"
    )

    with pytest.raises(
        TransactionRepositoryError,
        match="Unable to delete transactions",
    ):
        repository.delete_by_import_history_id(123)

    mock_conn.commit.assert_not_called()
    mock_conn.rollback.assert_not_called()

def test_delete_by_import_history_id_preserves_original_exception(
    repository,
    mock_cursor,
):
    original_error = Exception("database error")

    mock_cursor.execute.side_effect = original_error

    with pytest.raises(
        TransactionRepositoryError
    ) as exc_info:
        repository.delete_by_import_history_id(123)

    assert exc_info.value.__cause__ is original_error

def test_insert_transaction_success(
    repository,
    mock_conn,
):
    cursor = (
        mock_conn.cursor.return_value
        .__enter__.return_value
    )

    cursor.fetchone.return_value = (123,)

    result = repository.insert(
        Transaction(
            account_id=1,
            security_id=10,
            run_date="2026-06-17",
            settlement_date="2026-06-18",
            action="BUY",
            trade_type="TRADE",
            price=100.00,
            quantity=5,
            commission=1.00,
            fees=0.50,
            accrued_interest=0,
            amount=500.00,
            cash_balance=10000.00,
        )
    )

    assert result.id == 123
    assert result.account_id == 1
    assert result.security_id == 10
    assert result.action == "BUY"

    cursor.execute.assert_called_once()
    mock_conn.commit.assert_called_once()


def test_exists_returns_true_when_transaction_exists(
    repository,
    mock_conn,
):
    cursor = (
        mock_conn.cursor.return_value
        .__enter__.return_value
    )

    cursor.fetchone.return_value = (True,)

    result = repository.exists(
        Transaction(
            account_id=1,
            run_date="2026-06-17",
            security_id=10,
            amount=500.00,
            action="BUY",
            trade_type="TRADE",
        )
    )

    assert result is True

    cursor.execute.assert_called_once()


def test_exists_returns_false_when_transaction_missing(
    repository,
    mock_conn,
):
    cursor = (
        mock_conn.cursor.return_value
        .__enter__.return_value
    )

    cursor.fetchone.return_value = (False,)

    result = repository.exists(
        Transaction(
            account_id=1,
            run_date="2026-06-17",
            security_id=10,
            amount=500.00,
            action="BUY",
            trade_type="TRADE",
        )
    )

    assert result is False

    cursor.execute.assert_called_once()


def test_insert_commits_after_insert(
    repository,
    mock_conn,
):
    cursor = (
        mock_conn.cursor.return_value
        .__enter__.return_value
    )

    cursor.fetchone.return_value = (999,)

    repository.insert(
        Transaction(
            account_id=1,
            security_id=None,
            run_date="2026-06-17",
            settlement_date="2026-06-18",
            action="DIVIDEND",
            trade_type="CASH",
            price=None,
            quantity=None,
            commission=0,
            fees=0,
            accrued_interest=0,
            amount=250.00,
            cash_balance=12000.00,
        )
    )

    mock_conn.commit.assert_called_once()
from unittest.mock import MagicMock

import pytest

from repositories.transaction_repo import (
    TransactionRepository,
)


@pytest.fixture
def mock_conn():
    return MagicMock()


@pytest.fixture
def repository(mock_conn):
    return TransactionRepository(mock_conn)


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

    assert result == 123

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

    cursor.fetchone.return_value = (1,)

    result = repository.exists(
        account_id=1,
        run_date="2026-06-17",
        security_id=10,
        amount=500.00,
        action="BUY",
        trade_type="TRADE",
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

    cursor.fetchone.return_value = None

    result = repository.exists(
        account_id=1,
        run_date="2026-06-17",
        security_id=10,
        amount=500.00,
        action="BUY",
        trade_type="TRADE",
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

    mock_conn.commit.assert_called_once()
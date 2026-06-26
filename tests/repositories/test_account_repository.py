from unittest.mock import MagicMock

import psycopg
import pytest

from repositories.account_repo import (
    AccountRepository,
    AccountRepositoryError,
)


@pytest.fixture
def mock_conn():
    return MagicMock()


@pytest.fixture
def repository(mock_conn):
    return AccountRepository(mock_conn)


def test_get_by_number_returns_id(
    repository,
    mock_conn,
):
    cursor = mock_conn.cursor.return_value.__enter__.return_value

    cursor.fetchone.return_value = (123,)

    result = repository.get_by_number(
        "ABC123"
    )

    assert result == 123

    sql, params = cursor.execute.call_args.args

    assert "SELECT id" in sql
    assert "FROM accounts" in sql
    assert "WHERE account_number = %s" in sql
    assert params == ("ABC123",)


def test_get_by_number_returns_none_when_missing(
    repository,
    mock_conn,
):
    cursor = mock_conn.cursor.return_value.__enter__.return_value

    cursor.fetchone.return_value = None

    result = repository.get_by_number(
        "UNKNOWN"
    )

    assert result is None


def test_get_by_number_database_error(
    repository,
    mock_conn,
):
    cursor = mock_conn.cursor.return_value.__enter__.return_value

    cursor.execute.side_effect = psycopg.Error(
        "database unavailable"
    )

    with pytest.raises(
        AccountRepositoryError,
        match="Failed to lookup account",
    ):
        repository.get_by_number(
            "ABC123"
        )


def test_create_account(
    repository,
    mock_conn,
):
    cursor = mock_conn.cursor.return_value.__enter__.return_value

    cursor.fetchone.return_value = (456,)

    result = repository.create(
        account_number="ABC123",
        account_name="Rollover IRA",
        provider="Fidelity",
    )

    assert result == 456

    cursor.execute.assert_called_once()

    mock_conn.commit.assert_called_once()


def test_create_account_integrity_error(
    repository,
    mock_conn,
):
    cursor = mock_conn.cursor.return_value.__enter__.return_value

    cursor.execute.side_effect = (
        psycopg.IntegrityError(
            "duplicate account"
        )
    )

    with pytest.raises(
        AccountRepositoryError,
        match="already exists",
    ):
        repository.create(
            account_number="ABC123",
            account_name="Rollover IRA",
        )

    mock_conn.rollback.assert_called_once()


def test_get_or_create_existing_account(
    repository,
    mock_conn,
):
    result = repository.get_or_create(
        account_number="ABC123",
        account_name="Rollover IRA",
    )

    # force existing account
    repository.get_by_number = MagicMock(
        return_value=123
    )

    repository.create = MagicMock()

    result = repository.get_or_create(
        account_number="ABC123",
        account_name="Rollover IRA",
    )

    assert result == 123

    repository.create.assert_not_called()


def test_get_or_create_creates_missing_account(
    repository,
):
    repository.get_by_number = MagicMock(
        return_value=None
    )

    repository.create = MagicMock(
        return_value=789
    )

    result = repository.get_or_create(
        account_number="NEW123",
        account_name="Brokerage",
    )

    assert result == 789

    repository.create.assert_called_once_with(
        "NEW123",
        "Brokerage",
        "unknown",
    )
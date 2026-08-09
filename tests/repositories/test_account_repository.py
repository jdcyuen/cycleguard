from unittest.mock import MagicMock
import psycopg
import pytest

from repositories.account_repo import (
    AccountRepository,
    AccountRepositoryError,
)
from models.account import Account


@pytest.fixture
def mock_conn():
    return MagicMock()


@pytest.fixture
def repository(mock_conn):
    return AccountRepository(mock_conn)


def test_get_by_id_returns_account(repository, mock_conn):
    cursor = mock_conn.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = (123, "ABC123", "Rollover IRA", "Fidelity")

    result = repository.get_by_id(123)

    assert isinstance(result, Account)
    assert result.id == 123
    assert result.account_number == "ABC123"
    assert result.name == "Rollover IRA"
    assert result.institution == "Fidelity"

    sql, params = cursor.execute.call_args.args
    assert "SELECT id, account_number, name, institution" in sql
    assert "FROM cycleguard.accounts" in sql
    assert "WHERE id = %s" in sql
    assert params == (123,)


def test_get_by_id_returns_none_when_missing(repository, mock_conn):
    cursor = mock_conn.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = None

    result = repository.get_by_id(999)

    assert result is None


def test_get_by_id_database_error(repository, mock_conn):
    cursor = mock_conn.cursor.return_value.__enter__.return_value
    cursor.execute.side_effect = psycopg.Error("database unavailable")

    with pytest.raises(
        AccountRepositoryError,
        match="Failed to lookup account id=123",
    ):
        repository.get_by_id(123)


def test_get_by_name_returns_account(repository, mock_conn):
    cursor = mock_conn.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = (123, "ABC123", "Rollover IRA", "Fidelity")

    result = repository.get_by_name("Rollover IRA")

    assert isinstance(result, Account)
    assert result.id == 123
    assert result.name == "Rollover IRA"

    sql, params = cursor.execute.call_args.args
    assert "WHERE name = %s" in sql
    assert params == ("Rollover IRA",)


def test_get_by_name_returns_none_when_missing(repository, mock_conn):
    cursor = mock_conn.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = None

    result = repository.get_by_name("Missing Account")

    assert result is None


def test_get_by_name_database_error(repository, mock_conn):
    cursor = mock_conn.cursor.return_value.__enter__.return_value
    cursor.execute.side_effect = psycopg.Error("database unavailable")

    with pytest.raises(
        AccountRepositoryError,
        match="Failed to lookup account 'Rollover IRA'",
    ):
        repository.get_by_name("Rollover IRA")


def test_list_accounts(repository, mock_conn):
    cursor = mock_conn.cursor.return_value.__enter__.return_value
    cursor.fetchall.return_value = [
        (123, "ABC123", "Rollover IRA", "Fidelity"),
        (456, "XYZ456", "Roth IRA", "Fidelity"),
    ]

    result = repository.list_accounts()

    assert len(result) == 2
    assert result[0].name == "Rollover IRA"
    assert result[1].name == "Roth IRA"

    sql = cursor.execute.call_args.args[0]

    assert "SELECT id, account_number, name, institution" in sql
    assert "FROM cycleguard.accounts" in sql
    assert "ORDER BY name" in sql


def test_list_accounts_database_error(repository, mock_conn):
    cursor = mock_conn.cursor.return_value.__enter__.return_value
    cursor.execute.side_effect = psycopg.Error("database unavailable")

    with pytest.raises(
        AccountRepositoryError,
        match="Failed to list accounts",
    ):
        repository.list_accounts()

def test_list_accounts_empty(repository, mock_conn):
    cursor = mock_conn.cursor.return_value.__enter__.return_value
    cursor.fetchall.return_value = []

    result = repository.list_accounts()

    assert result == []

def test_create_account(repository, mock_conn):
    cursor = mock_conn.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = (456, "ABC123", "Rollover IRA", "Fidelity")

    result = repository.create(
        Account(
            account_number="ABC123",
            name="Rollover IRA",
            institution="Fidelity",
        )
    )

    assert isinstance(result, Account)
    assert result.id == 456
    assert result.name == "Rollover IRA"

    cursor.execute.assert_called_once()

    sql, params = cursor.execute.call_args.args

    assert "INSERT INTO cycleguard.accounts" in sql
    assert "VALUES (%s, %s, %s)" in sql
    assert "RETURNING id, account_number, name, institution" in sql

    assert params == (
        "ABC123",
        "Rollover IRA",
        "Fidelity",
    )

    mock_conn.commit.assert_called_once()
    mock_conn.rollback.assert_not_called()


def test_create_account_integrity_error(repository, mock_conn):
    cursor = mock_conn.cursor.return_value.__enter__.return_value
    cursor.execute.side_effect = psycopg.IntegrityError("duplicate account")

    with pytest.raises(
        AccountRepositoryError,
        match="already exists",
    ):
        repository.create(
            Account(
                account_number="ABC123",
                name="Rollover IRA",
                institution="Fidelity",
            )
        )

    mock_conn.rollback.assert_called_once()
    mock_conn.commit.assert_not_called()


def test_create_account_database_error(repository, mock_conn):
    cursor = mock_conn.cursor.return_value.__enter__.return_value
    cursor.execute.side_effect = psycopg.Error("database unavailable")

    with pytest.raises(
        AccountRepositoryError,
        match="Failed to create account 'Rollover IRA'",
    ):
        repository.create(
            Account(
                account_number="ABC123",
                name="Rollover IRA",
                institution="Fidelity",
            )
        )

    mock_conn.rollback.assert_called_once()
    mock_conn.commit.assert_not_called()
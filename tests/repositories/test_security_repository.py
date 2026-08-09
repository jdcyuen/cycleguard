from unittest.mock import MagicMock
import psycopg
import pytest

from repositories.security_repo import (
    SecurityRepository,
    SecurityRepositoryError,
)
from models.security import Security


@pytest.fixture
def mock_conn():
    return MagicMock()


@pytest.fixture
def repository(mock_conn):
    return SecurityRepository(mock_conn)


def test_get_by_symbol_returns_security(repository, mock_conn):
    cursor = mock_conn.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = (123, "AAPL", "Apple Inc")

    result = repository.get_by_symbol("AAPL")

    assert isinstance(result, Security)
    assert result.id == 123
    assert result.symbol == "AAPL"
    assert result.description == "Apple Inc"

    sql, params = cursor.execute.call_args.args
    assert "SELECT id, symbol, description" in sql
    assert "FROM cycleguard.securities" in sql
    assert "WHERE symbol = %s" in sql
    assert params == ("AAPL",)


def test_get_by_symbol_returns_none(repository, mock_conn):
    cursor = mock_conn.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = None

    result = repository.get_by_symbol("UNKNOWN")

    assert result is None


def test_get_by_symbol_database_error(repository, mock_conn):
    cursor = mock_conn.cursor.return_value.__enter__.return_value
    cursor.execute.side_effect = psycopg.Error("database error")

    with pytest.raises(SecurityRepositoryError, match="Failed to lookup security 'AAPL'"):
        repository.get_by_symbol("AAPL")


def test_get_by_id_returns_security(repository, mock_conn):
    cursor = mock_conn.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = (123, "AAPL", "Apple Inc")

    result = repository.get_by_id(123)

    assert isinstance(result, Security)
    assert result.id == 123
    assert result.symbol == "AAPL"
    assert result.description == "Apple Inc"

    sql, params = cursor.execute.call_args.args
    assert "SELECT" in sql
    assert "FROM cycleguard.securities" in sql
    assert "WHERE id = %s" in sql
    assert params == (123,)


def test_get_by_id_returns_none(repository, mock_conn):
    cursor = mock_conn.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = None

    result = repository.get_by_id(999)

    assert result is None


def test_get_by_id_database_error(repository, mock_conn):
    cursor = mock_conn.cursor.return_value.__enter__.return_value
    cursor.execute.side_effect = psycopg.Error("database error")

    with pytest.raises(SecurityRepositoryError, match="Unable to lookup security"):
        repository.get_by_id(123)


def test_upsert_success(repository, mock_conn):
    cursor = mock_conn.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = (123, "AAPL", "Apple Inc", "Stock")

    security = Security(symbol="AAPL", description="Apple Inc", asset_type="Stock")
    result = repository.upsert(security)

    assert isinstance(result, Security)
    assert result.id == 123
    assert result.symbol == "AAPL"
    assert result.description == "Apple Inc"
    assert result.asset_type == "Stock"

    sql, params = cursor.execute.call_args.args
    assert "INSERT INTO cycleguard.securities" in sql
    assert "ON CONFLICT (symbol)" in sql
    assert params == ("AAPL", "Apple Inc", "Stock")
    mock_conn.commit.assert_called_once()


def test_upsert_database_error(repository, mock_conn):
    cursor = mock_conn.cursor.return_value.__enter__.return_value
    cursor.execute.side_effect = psycopg.Error("database error")

    security = Security(symbol="AAPL")
    with pytest.raises(SecurityRepositoryError, match="Unable to create or update security 'AAPL'"):
        repository.upsert(security)

    mock_conn.rollback.assert_called_once()


def test_list_securities(repository, mock_conn):

    cursor = mock_conn.cursor.return_value.__enter__.return_value
    cursor.fetchall.return_value = [
        (123, "AAPL", "Apple Inc"),
        (456, "MSFT", "Microsoft Corp"),
    ]

    result = repository.list_securities()

    assert len(result) == 2
    assert result[0].symbol == "AAPL"
    assert result[1].symbol == "MSFT"

    sql = cursor.execute.call_args.args[0]

    assert "FROM cycleguard.securities" in sql
    assert "ORDER BY symbol" in sql


def test_list_securities_database_error(repository, mock_conn):
    cursor = mock_conn.cursor.return_value.__enter__.return_value
    cursor.execute.side_effect = psycopg.Error("database error")

    with pytest.raises(SecurityRepositoryError, match="Unable to retrieve securities"):
        repository.list_securities()


def test_update_if_missing_success(repository, mock_conn):
    cursor = mock_conn.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = (123, "AAPL", "Apple Inc", "Stock")

    security = Security(id=123, symbol="AAPL", description="Apple Inc", asset_type="Stock")
    result = repository.update_if_missing(security)

    assert isinstance(result, Security)
    assert result.id == 123
    assert result.symbol == "AAPL"
    assert result.description == "Apple Inc"
    assert result.asset_type == "Stock"

    sql, params = cursor.execute.call_args.args
    assert "UPDATE cycleguard.securities" in sql
    assert "SET" in sql
    assert "COALESCE" in sql
    assert params == ("Apple Inc", "Stock", 123)
    mock_conn.commit.assert_called_once()
    mock_conn.rollback.assert_not_called()


def test_update_if_missing_not_found(repository, mock_conn):
    cursor = mock_conn.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = None

    security = Security(id=999, symbol="AAPL")
    with pytest.raises(SecurityRepositoryError, match="Security id=999 not found"):
        repository.update_if_missing(security)

    mock_conn.rollback.assert_called_once()


def test_update_if_missing_database_error(repository, mock_conn):
    cursor = mock_conn.cursor.return_value.__enter__.return_value
    cursor.execute.side_effect = psycopg.Error("database error")

    security = Security(
        id=123,
        symbol="AAPL",
        description="Apple Inc",
        asset_type="Stock",
    )

    with pytest.raises(
        SecurityRepositoryError,
        match="Unable to update security 'AAPL'",
    ):
        repository.update_if_missing(security)

    mock_conn.rollback.assert_called_once()
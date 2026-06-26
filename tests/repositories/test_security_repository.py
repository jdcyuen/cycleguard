from unittest.mock import MagicMock

import psycopg
import pytest

from repositories.security_repo import (
    SecurityRepository,
    SecurityRepositoryError,
)


@pytest.fixture
def mock_conn():
    return MagicMock()


@pytest.fixture
def repository(mock_conn):
    return SecurityRepository(mock_conn)


def test_get_by_ticker_returns_id(
    repository,
    mock_conn,
):
    cursor = (
        mock_conn.cursor.return_value
        .__enter__.return_value
    )

    cursor.fetchone.return_value = (123,)

    result = repository.get_by_ticker(
        "AAPL"
    )

    assert result == 123

    sql, params = cursor.execute.call_args.args

    assert "SELECT id" in sql
    assert "FROM securities" in sql
    assert "WHERE ticker = %s" in sql
    assert params == ("AAPL",)



def test_get_by_ticker_returns_none(
    repository,
    mock_conn,
):
    cursor = (
        mock_conn.cursor.return_value
        .__enter__.return_value
    )

    cursor.fetchone.return_value = None

    result = repository.get_by_ticker(
        "UNKNOWN"
    )

    assert result is None



def test_get_by_ticker_database_error(
    repository,
    mock_conn,
):
    cursor = (
        mock_conn.cursor.return_value
        .__enter__.return_value
    )

    cursor.execute.side_effect = (
        psycopg.Error()
    )

    with pytest.raises(
        SecurityRepositoryError
    ) as exc_info:
        repository.get_by_ticker(
            "AAPL"
        )

    assert (
        "Failed to lookup security"
        in str(exc_info.value)
    )


def test_create_success(
    repository,
    mock_conn,
):
    cursor = (
        mock_conn.cursor.return_value
        .__enter__.return_value
    )

    cursor.fetchone.return_value = (456,)

    result = repository.create(
        ticker="AAPL",
        description="Apple Inc",
        asset_type="Stock",
    )

    assert result == 456

    sql, params = cursor.execute.call_args.args

    assert "INSERT INTO securities" in sql
    assert "RETURNING id" in sql

    assert params == (
        "AAPL",
        "Apple Inc",
        "Stock",
    )

    mock_conn.commit.assert_called_once()
    mock_conn.rollback.assert_not_called()


def test_create_integrity_error(
    repository,
    mock_conn,
):
    cursor = (
        mock_conn.cursor.return_value
        .__enter__.return_value
    )

    cursor.execute.side_effect = (
        psycopg.IntegrityError()
    )

    with pytest.raises(
        SecurityRepositoryError
    ) as exc_info:
        repository.create("AAPL")

    assert (
        "already exists"
        in str(exc_info.value)
    )

    mock_conn.rollback.assert_called_once()
    mock_conn.commit.assert_not_called()    

def test_create_database_error(
    repository,
    mock_conn,
):
    cursor = (
        mock_conn.cursor.return_value
        .__enter__.return_value
    )

    cursor.execute.side_effect = (
        psycopg.Error()
    )

    with pytest.raises(
        SecurityRepositoryError
    ) as exc_info:
        repository.create("AAPL")

    assert (
        "Failed to create security"
        in str(exc_info.value)
    )

    mock_conn.rollback.assert_called_once()
    mock_conn.commit.assert_not_called()



def test_get_or_create_existing(
    repository,
    monkeypatch,
):
    monkeypatch.setattr(
        repository,
        "get_by_ticker",
        lambda ticker: 123,
    )

    result = repository.get_or_create(
        "AAPL"
    )

    assert result == 123

def test_get_or_create_creates_new(
    repository,
    monkeypatch,
):
    monkeypatch.setattr(
        repository,
        "get_by_ticker",
        lambda ticker: None,
    )

    monkeypatch.setattr(
        repository,
        "create",
        lambda ticker, description, asset_type: 456,
    )

    result = repository.get_or_create(
        "AAPL",
        "Apple Inc",
        "Stock",
    )

    assert result == 456
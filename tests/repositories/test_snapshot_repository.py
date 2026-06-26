from unittest.mock import MagicMock

import pytest

from repositories.snapshot_repo import (
    SnapshotRepository,
)


@pytest.fixture
def mock_conn():
    return MagicMock()


@pytest.fixture
def repository(mock_conn):
    return SnapshotRepository(mock_conn)


def test_get_by_date_returns_id(
    repository,
    mock_conn,
):
    cursor = (
        mock_conn.cursor.return_value
        .__enter__.return_value
    )

    cursor.fetchone.return_value = (123,)

    result = repository.get_by_date(
        "2025-01-31"
    )

    assert result == 123

    sql, params = cursor.execute.call_args.args

    assert "SELECT id" in sql
    assert "FROM snapshots" in sql
    assert "WHERE snapshot_date = %s" in sql

    assert params == (
        "2025-01-31",
    )

def test_get_by_date_returns_none(
    repository,
    mock_conn,
):
    cursor = (
        mock_conn.cursor.return_value
        .__enter__.return_value
    )

    cursor.fetchone.return_value = None

    result = repository.get_by_date(
        "2025-01-31"
    )

    assert result is None

def test_create_returns_snapshot_id(
    repository,
    mock_conn,
):
    cursor = (
        mock_conn.cursor.return_value
        .__enter__.return_value
    )

    cursor.fetchone.return_value = (456,)

    result = repository.create(
        "2025-01-31"
    )

    assert result == 456

    sql, params = cursor.execute.call_args.args

    assert "INSERT INTO snapshots" in sql
    assert "RETURNING id" in sql

    assert params == (
        "2025-01-31",
    )

    mock_conn.commit.assert_called_once()


def test_ensure_not_exists_when_missing(
    repository,
    monkeypatch,
):
    monkeypatch.setattr(
        repository,
        "get_by_date",
        lambda snapshot_date: None,
    )

    repository.ensure_not_exists(
        "2025-01-31"
    )

def test_ensure_not_exists_raises(
    repository,
    monkeypatch,
):
    monkeypatch.setattr(
        repository,
        "get_by_date",
        lambda snapshot_date: 123,
    )

    with pytest.raises(
        ValueError
    ) as exc_info:
        repository.ensure_not_exists(
            "2025-01-31"
        )

    assert (
        "Snapshot already exists"
        in str(exc_info.value)
    )

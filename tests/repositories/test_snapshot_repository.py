from unittest.mock import MagicMock

import pytest

from repositories.snapshot_repo import (
    SnapshotRepository,
)
from models.snapshot import Snapshot

import psycopg

from repositories.snapshot_repo import (
    SnapshotRepositoryError,
)



@pytest.fixture
def mock_conn():
    return MagicMock()

@pytest.fixture
def mock_cursor():
    return MagicMock()


@pytest.fixture
def repository(mock_conn, mock_cursor):
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    return SnapshotRepository(mock_conn)


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

    assert "DELETE FROM cycleguard.snapshots" in sql
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
        SnapshotRepositoryError,
        match="Unable to delete snapshots",
    ):
        repository.delete_by_import_history_id(123)

    mock_conn.commit.assert_not_called()
    mock_conn.rollback.assert_not_called()


def test_get_by_date_returns_snapshot(
    repository,
    mock_conn,
):
    cursor = (
        mock_conn.cursor.return_value
        .__enter__.return_value
    )

    cursor.fetchone.return_value = (123, "2025-01-31")

    result = repository.get_by_date(
        "2025-01-31"
    )

    assert isinstance(result, Snapshot)
    assert result.id == 123
    assert result.snapshot_date == "2025-01-31"

    sql, params = cursor.execute.call_args.args

    assert "SELECT" in sql
    assert "id" in sql
    assert "snapshot_date" in sql
    assert "FROM cycleguard.snapshots" in sql
    assert "WHERE snapshot_date = %s" in sql

    assert params == (
        "2025-01-31",
    )
    mock_conn.commit.assert_not_called()


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
    mock_conn.commit.assert_not_called()


def test_create_returns_snapshot(
    repository,
    mock_conn,
):
    cursor = (
        mock_conn.cursor.return_value
        .__enter__.return_value
    )

    cursor.fetchone.return_value = (456, "2025-01-31")

    result = repository.create(
        Snapshot(snapshot_date="2025-01-31")
    )

    assert isinstance(result, Snapshot)
    assert result.id == 456
    assert result.snapshot_date == "2025-01-31"

    sql, params = cursor.execute.call_args.args

    assert "INSERT INTO cycleguard.snapshots" in sql
    assert "RETURNING id" in sql

    assert params == (
        "2025-01-31",
    )

    # Verify transaction behavior
    mock_conn.commit.assert_called_once()
    mock_conn.rollback.assert_not_called()


def test_ensure_not_exists_when_missing(
    repository,
    monkeypatch,
):
    mock_get = MagicMock(return_value=None)

    monkeypatch.setattr(
        repository,
        "get_by_date",
        mock_get,
    )

    repository.ensure_not_exists(
        "2025-01-31"
    )

    mock_get.assert_called_once_with(
        "2025-01-31"
    )

def test_ensure_not_exists_raises(
    repository,
    monkeypatch,
):
    monkeypatch.setattr(
        repository,
        "get_by_date",
        lambda snapshot_date: Snapshot(id=123, snapshot_date="2025-01-31"),
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

def test_get_by_date_database_error(
    repository,
    mock_conn,
):
    cursor = (
        mock_conn.cursor.return_value
        .__enter__.return_value
    )

    cursor.execute.side_effect = psycopg.Error()

    with pytest.raises(
        SnapshotRepositoryError
    ) as exc_info:
        repository.get_by_date(
            "2025-01-31"
        )

    assert (
        "Failed to lookup snapshot"
        in str(exc_info.value)
    )

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
        SnapshotRepositoryError
    ) as exc_info:
        repository.create(
            Snapshot(snapshot_date="2025-01-31")
        )

    assert (
        "Snapshot already exists"
        in str(exc_info.value)
    )

    mock_conn.rollback.assert_called_once()


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
        SnapshotRepositoryError
    ) as exc_info:
        repository.create(
            Snapshot(snapshot_date="2025-01-31")
        )

    assert (
        "Failed to create snapshot"
        in str(exc_info.value)
    )

    mock_conn.rollback.assert_called_once()













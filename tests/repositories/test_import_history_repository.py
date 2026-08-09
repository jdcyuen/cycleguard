from unittest.mock import MagicMock
import pytest
from datetime import date
from datetime import datetime

from repositories.import_history_repo import (
    ImportHistoryRepository,
    ImportHistoryRepositoryError,
)

from models.importhistory import ImportHistory


@pytest.fixture
def mock_conn():
    return MagicMock()


@pytest.fixture
def repository(mock_conn):
    return ImportHistoryRepository(mock_conn)


@pytest.fixture
def import_history():
    return ImportHistory(
        account_id=1,
        import_type="POSITIONS",
        institution="Fidelity",
        filename="positions.csv",
        file_hash="abc123",
        snapshot_date=date(2025, 12, 31),
        import_timestamp=None,
        rows_read=100,
        rows_imported=0,
        rows_skipped=0,
        status="SUCCESS",
        elapsed_ms=0,
        error_message=None,
    )

def test_insert_success(
    repository,
    mock_conn,
    import_history,
):
    """
    Verify insert creates an ImportHistory record.
    """

    mock_cursor = MagicMock()

    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    mock_cursor.fetchone.return_value = (
        10,                                 # id
        1,                                  # account_id
        "POSITIONS",                        # import_type
        "Fidelity",                         # institution
        "positions.csv",                    # filename
        "abc123",                           # file_hash
        date(2025, 12, 31),                 # snapshot_date
        datetime(2025, 12, 31, 10, 0, 0),   # import_timestamp
        0,                                  # rows_read
        0,                                  # rows_imported
        0,                                  # rows_skipped
        "SUCCESS",                          # status
        0,                                  # elapsed_ms
        None,                               # error_message
    )

    result = repository.insert(import_history)

    assert result.id == 10
    assert result.account_id == 1
    assert result.import_type == "POSITIONS"
    assert result.institution == "Fidelity"
    assert result.filename == "positions.csv"
    assert result.file_hash == "abc123"
    assert result.snapshot_date == date(2025, 12, 31)
    assert result.import_timestamp == datetime(
        2025,
        12,
        31,
        10,
        0,
        0,
    )
    assert result.rows_read == 0
    assert result.rows_imported == 0
    assert result.rows_skipped == 0
    assert result.status == "SUCCESS"
    assert result.elapsed_ms == 0
    assert result.error_message is None

    mock_cursor.execute.assert_called_once()
    mock_conn.commit.assert_called_once()


def test_insert_failure_rolls_back(
    repository,
    mock_conn,
    import_history,
):
    """
    Verify insert rolls back the transaction
    when a database error occurs.
    """

    mock_cursor = MagicMock()

    mock_conn.cursor.return_value.__enter__.return_value = (
        mock_cursor
    )

    mock_cursor.execute.side_effect = Exception(
        "database failure"
    )

    with pytest.raises(
        ImportHistoryRepositoryError,
        match="Unable to insert import history record",
    ):
        repository.insert(import_history)

    mock_conn.rollback.assert_called_once()

    mock_conn.commit.assert_not_called()

    mock_cursor.execute.assert_called_once()



def test_complete_import_success(
    repository,
    mock_conn,
):
    """
    Verify complete_import updates the import
    history record.
    """

    mock_cursor = MagicMock()

    mock_conn.cursor.return_value.__enter__.return_value = (
        mock_cursor
    )

    repository.complete_import(
        import_id=10,
        rows_read=100,
        rows_imported=98,
        rows_skipped=2,
        status="SUCCESS",
        elapsed_ms=1534,
        error_message=None,
    )

    mock_cursor.execute.assert_called_once()

    mock_conn.commit.assert_called_once()



def test_complete_import_failure(
    repository,
    mock_conn,
):
    """
    Verify complete_import rolls back the
    transaction when a database error occurs.
    """

    mock_cursor = MagicMock()

    mock_conn.cursor.return_value.__enter__.return_value = (
        mock_cursor
    )

    mock_cursor.execute.side_effect = Exception(
        "update failed"
    )

    with pytest.raises(
        ImportHistoryRepositoryError,
        match="Unable to complete import.",
    ):
        repository.complete_import(
            import_id=10,
            rows_read=100,
            rows_imported=98,
            rows_skipped=2,
            status="FAILED",
            elapsed_ms=1534,
            error_message="database failure",
        )

    mock_conn.rollback.assert_called_once()

    mock_conn.commit.assert_not_called()

    mock_cursor.execute.assert_called_once()



def test_get_by_id_found(
    repository,
    mock_conn,
):
    """
    Verify retrieving an import history
    record by id.
    """

    mock_cursor = MagicMock()

    mock_conn.cursor.return_value.__enter__.return_value = (
        mock_cursor
    )

    mock_cursor.fetchone.return_value = (
        10,                                 # id
        1,                                  # account_id
        "POSITIONS",                        # import_type
        "Fidelity",                         # institution
        "positions.csv",                    # filename
        "abc123",                           # file_hash
        date(2025, 12, 31),                 # snapshot_date
        datetime(2025, 12, 31, 10, 0, 0),   # import_timestamp
        100,                                # rows_read
        98,                                 # rows_imported
        2,                                  # rows_skipped
        "SUCCESS",                          # status
        1534,                               # elapsed_ms
        None,                               # error_message
    )

    result = repository.get_by_id(10)

    assert isinstance(result, ImportHistory)

    assert result.id == 10
    assert result.account_id == 1
    assert result.import_type == "POSITIONS"
    assert result.institution == "Fidelity"
    assert result.filename == "positions.csv"
    assert result.file_hash == "abc123"

    assert result.snapshot_date == date(
        2025,
        12,
        31,
    )

    assert result.import_timestamp == datetime(
        2025,
        12,
        31,
        10,
        0,
        0,
    )

    assert result.rows_read == 100
    assert result.rows_imported == 98
    assert result.rows_skipped == 2

    assert result.status == "SUCCESS"
    assert result.elapsed_ms == 1534
    assert result.error_message is None

    mock_cursor.execute.assert_called_once()



def test_get_by_id_not_found(
    repository,
    mock_conn,
):
    """
    Verify missing import history record
    returns None.
    """

    mock_cursor = MagicMock()

    mock_conn.cursor.return_value.__enter__.return_value = (
        mock_cursor
    )

    mock_cursor.fetchone.return_value = None

    result = repository.get_by_id(999)

    assert result is None

    mock_cursor.execute.assert_called_once()



def test_exists_true(
    repository,
    mock_conn,
):
    """
    Verify duplicate import detection.
    """

    mock_cursor = MagicMock()

    mock_conn.cursor.return_value.__enter__.return_value = (
        mock_cursor
    )

    mock_cursor.fetchone.return_value = (True,)

    result = repository.exists(
        account_id=1,
        import_type="POSITIONS",
        file_hash="abc123",
    )

    assert result is True

    mock_cursor.execute.assert_called_once()



def test_exists_false(
    repository,
    mock_conn,
):
    """
    Verify a new import is not flagged
    as a duplicate.
    """

    mock_cursor = MagicMock()

    mock_conn.cursor.return_value.__enter__.return_value = (
        mock_cursor
    )

    mock_cursor.fetchone.return_value = (False,)

    result = repository.exists(
        account_id=1,
        import_type="POSITIONS",
        file_hash="xyz999",
    )

    assert result is False

    mock_cursor.execute.assert_called_once()



def test_get_latest_with_type(
    repository,
    mock_conn,
):
    """
    Verify retrieving the latest import
    history record for a specific import type.
    """

    mock_cursor = MagicMock()

    mock_conn.cursor.return_value.__enter__.return_value = (
        mock_cursor
    )

    mock_cursor.fetchone.return_value = (
        10,                                 # id
        1,                                  # account_id
        "POSITIONS",                        # import_type
        "Fidelity",                         # institution
        "positions.csv",                    # filename
        "abc123",                           # file_hash
        date(2025, 12, 31),                 # snapshot_date
        datetime(2025, 12, 31, 10, 0, 0),   # import_timestamp
        100,                                # rows_read
        98,                                 # rows_imported
        2,                                  # rows_skipped
        "SUCCESS",                          # status
        1534,                               # elapsed_ms
        None,                               # error_message
    )

    result = repository.get_latest(
        import_type="POSITIONS",
    )

    assert isinstance(result, ImportHistory)

    assert result.id == 10
    assert result.account_id == 1
    assert result.import_type == "POSITIONS"
    assert result.institution == "Fidelity"
    assert result.filename == "positions.csv"
    assert result.file_hash == "abc123"

    assert result.snapshot_date == date(
        2025,
        12,
        31,
    )

    assert result.import_timestamp == datetime(
        2025,
        12,
        31,
        10,
        0,
        0,
    )

    assert result.rows_read == 100
    assert result.rows_imported == 98
    assert result.rows_skipped == 2

    assert result.status == "SUCCESS"
    assert result.elapsed_ms == 1534
    assert result.error_message is None

    mock_cursor.execute.assert_called_once()



def test_get_latest_none(
    repository,
    mock_conn,
):
    """
    Verify get_latest returns None when
    no import history records exist.
    """

    mock_cursor = MagicMock()

    mock_conn.cursor.return_value.__enter__.return_value = (
        mock_cursor
    )

    mock_cursor.fetchone.return_value = None

    result = repository.get_latest()

    assert result is None

    mock_cursor.execute.assert_called_once()

def test_get_latest_with_type(
    repository,
    mock_conn,
):
    """
    Verify latest import by type.
    """

    mock_cursor = MagicMock()

    mock_conn.cursor.return_value.__enter__.return_value = (
        mock_cursor
    )

    mock_cursor.fetchone.return_value = (
        10,                                 # id
        1,                                  # account_id
        "POSITIONS",                        # import_type
        "Fidelity",                         # institution
        "positions.csv",                    # filename
        "abc123",                           # file_hash
        date(2025, 12, 31),                 # snapshot_date
        datetime(2025, 12, 31, 10, 0, 0),   # import_timestamp
        100,                                # rows_read
        98,                                 # rows_imported
        2,                                  # rows_skipped
        "SUCCESS",                          # status
        1534,                               # elapsed_ms
        None,                               # error_message
    )

    result = repository.get_latest(
        import_type="POSITIONS"
    )

    assert result is not None
    assert result.id == 10
    assert result.account_id == 1
    assert result.import_type == "POSITIONS"
    assert result.institution == "Fidelity"
    assert result.filename == "positions.csv"
    assert result.file_hash == "abc123"
    assert result.snapshot_date == date(2025, 12, 31)
    assert result.import_timestamp == datetime(
        2025,
        12,
        31,
        10,
        0,
        0,
    )
    assert result.rows_read == 100
    assert result.rows_imported == 98
    assert result.rows_skipped == 2
    assert result.status == "SUCCESS"
    assert result.elapsed_ms == 1534
    assert result.error_message is None

def test_get_latest_none(
    repository,
    mock_conn,
):
    """
    Verify no imports returns None.
    """

    mock_cursor = MagicMock()

    mock_conn.cursor.return_value.__enter__.return_value = (
        mock_cursor
    )

    mock_cursor.fetchone.return_value = None

    result = repository.get_latest()

    assert result is None



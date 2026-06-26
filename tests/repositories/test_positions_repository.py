from unittest.mock import MagicMock

import psycopg
import pytest

from repositories.position_repo import (
    PositionRepository,
    PositionRepositoryError
)



@pytest.fixture
def mock_conn():
    return MagicMock()


@pytest.fixture
def repository(mock_conn):
    return PositionRepository(mock_conn)

def test_insert_success(
    repository,
    mock_conn,
):
    cursor = (
        mock_conn.cursor.return_value
        .__enter__.return_value
    )

    repository.insert(
        snapshot_id=1,
        account_id=2,
        security_id=3,
        quantity=100,
        avg_cost=50.0,
    )

    sql, params = cursor.execute.call_args.args

    assert "INSERT INTO positions" in sql
    assert "snapshot_id" in sql
    assert "security_id" in sql

    assert params == (
        1,      # snapshot_id
        2,      # account_id
        3,      # security_id
        100,    # quantity
        50.0,   # avg_cost
        None,   # cost_basis_total
        None,   # market_value
        None,   # percent_of_account
        None,   # daily_gain
        None,   # daily_gain_pct
        None,   # total_gain
        None,   # total_gain_pct
    )

    mock_conn.commit.assert_called_once()
    mock_conn.rollback.assert_not_called()

def test_insert_integrity_error(repository, mock_conn):
    """
    Test that IntegrityError is caught and rolled back.
    """
    cursor = (
        mock_conn.cursor.return_value
        .__enter__.return_value
    )

    # Make execute raise IntegrityError
    cursor.execute.side_effect = psycopg.IntegrityError("duplicate key")

    with pytest.raises(PositionRepositoryError, match="already exists"):
        repository.insert(
            snapshot_id=1,
            account_id=2,
            security_id=3,
        )

    mock_conn.commit.assert_not_called()
    mock_conn.rollback.assert_called_once()


def test_insert_database_error(
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
        PositionRepositoryError
    ) as exc_info:
        repository.insert(
            snapshot_id=1,
            account_id=2,
            security_id=3,
        )

    assert (
        "Failed to insert position"
        in str(exc_info.value)
    )

    mock_conn.rollback.assert_called_once()
    mock_conn.commit.assert_not_called()
from unittest.mock import MagicMock

import psycopg
import pytest

from repositories.position_repo import (
    PositionRepository,
    PositionRepositoryError
)
from models.position import Position



@pytest.fixture
def mock_conn():
    return MagicMock()


@pytest.fixture
def repository(mock_conn):
    return PositionRepository(mock_conn)

# ---------------------------------------------------------------------
# insert()
# ---------------------------------------------------------------------

def test_insert_success(
    repository,
    mock_conn,
):
    cursor = (
        mock_conn.cursor.return_value
        .__enter__.return_value
    )

    repository.insert(
        Position(
            snapshot_id=1,
            account_id=2,
            security_id=3,
            quantity=100,
            ave_cost=50.0,
            cost_basis_total=None,
            current_value=None,
            percent_of_account=None,
            daily_gain=None,
            daily_gain_pct=None,
            total_gain=None,
            total_gain_pct=None,
        )
    )

    sql, params = cursor.execute.call_args.args

    assert "INSERT INTO cycleguard.positions" in sql
    assert "snapshot_id" in sql
    assert "account_id" in sql
    assert "security_id" in sql
    assert "quantity" in sql
    assert "avg_cost" in sql
    assert "current_value" in sql

    assert params == (
        1,      # snapshot_id
        2,      # account_id
        3,      # security_id
        100,    # quantity
        50.0,   # avg_cost
        None,   # cost_basis_total
        None,   # current_value
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
            Position(
                snapshot_id=1,
                account_id=2,
                security_id=3,
            )
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
        PositionRepositoryError,
        match="Failed to insert position",
    ) :
        repository.insert(
            Position(
                snapshot_id=1,
                account_id=2,
                security_id=3,
            )
        )

    mock_conn.rollback.assert_called_once()
    mock_conn.commit.assert_not_called()


# ---------------------------------------------------------------------
# get_by_snapshot()
# ---------------------------------------------------------------------

def test_get_by_snapshot_success(repository, mock_conn):
    cursor = (
        mock_conn.cursor.return_value
        .__enter__.return_value
    )

    cursor.fetchall.return_value = [
        (
            1,          # id
            2,          # account_id
            3,          # security_id
            4,          # snapshot_id
            100,        # quantity
            50.0,       # avg_cost
            5000.0,     # cost_basis_total
            5500.0,     # current_value
            10.5,       # percent_of_account
            100.0,      # daily_gain
            2.0,        # daily_gain_pct
            500.0,      # total_gain
            10.0,       # total_gain_pct
        )
    ]

    positions = repository.get_by_snapshot(4)

    cursor.execute.assert_called_once()

    sql, params = cursor.execute.call_args.args

    assert "SELECT" in sql
    assert "FROM cycleguard.positions" in sql
    assert params == (4,)

    assert len(positions) == 1

    position = positions[0]

    assert position.id == 1
    assert position.account_id == 2
    assert position.security_id == 3
    assert position.snapshot_id == 4
    assert position.quantity == 100
    assert position.ave_cost == 50.0
    assert position.cost_basis_total == 5000.0
    assert position.current_value == 5500.0


def test_get_by_snapshot_database_error(repository, mock_conn):
    cursor = (
        mock_conn.cursor.return_value
        .__enter__.return_value
    )

    cursor.execute.side_effect = psycopg.Error()

    with pytest.raises(
        PositionRepositoryError,
        match="Failed retrieving positions",
    ):
        repository.get_by_snapshot(1)


# ---------------------------------------------------------------------
# delete_by_snapshot()
# ---------------------------------------------------------------------

def test_delete_by_snapshot_success(repository, mock_conn):
    cursor = (
        mock_conn.cursor.return_value
        .__enter__.return_value
    )

    cursor.rowcount = 5

    rows = repository.delete_by_snapshot(1)

    cursor.execute.assert_called_once()

    sql, params = cursor.execute.call_args.args

    assert "DELETE FROM cycleguard.positions" in sql
    assert params == (1,)

    assert rows == 5

    mock_conn.commit.assert_called_once()
    mock_conn.rollback.assert_not_called()


def test_delete_by_snapshot_database_error(repository, mock_conn):
    cursor = (
        mock_conn.cursor.return_value
        .__enter__.return_value
    )

    cursor.execute.side_effect = psycopg.Error()

    with pytest.raises(
        PositionRepositoryError,
        match="Failed deleting positions",
    ):
        repository.delete_by_snapshot(1)

    mock_conn.rollback.assert_called_once()
    mock_conn.commit.assert_not_called()
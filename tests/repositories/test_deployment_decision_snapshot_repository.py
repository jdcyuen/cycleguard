from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock
import psycopg
import pytest

from models.deployment_decision_snapshot import (
    DeploymentDecisionSnapshot,
)
from repositories.deployment_decision_snapshot_repository import (
    DeploymentDecisionSnapshotRepository,
    DeploymentDecisionSnapshotRepositoryError,
)


@pytest.fixture
def mock_conn():
    return MagicMock()


@pytest.fixture
def repository(mock_conn):
    return DeploymentDecisionSnapshotRepository(mock_conn)


def test_create_deployment_decision_snapshot(
    repository,
    mock_conn,
):
    cursor = mock_conn.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = (123,)

    snapshot = DeploymentDecisionSnapshot(
        deployment_decision_id=10,
        snapshot_date=date(2026, 9, 6),
        recommended_amount=Decimal("25000"),
        actual_amount_deployed=Decimal("10000"),
    )

    result = repository.create(snapshot)

    assert result == 123

    cursor.execute.assert_called_once()

    sql, params = cursor.execute.call_args.args

    assert (
        "INSERT INTO cycleguard.deployment_decision_snapshot"
        in sql
    )
    assert "VALUES (%s, %s, %s, %s)" in sql
    assert "RETURNING deployment_decision_snapshot_id" in sql

    assert params == (
        10,
        date(2026, 9, 6),
        Decimal("25000"),
        Decimal("10000"),
    )

    mock_conn.commit.assert_called_once()
    mock_conn.rollback.assert_not_called()


def test_create_deployment_decision_snapshot_database_error(
    repository,
    mock_conn,
):
    cursor = mock_conn.cursor.return_value.__enter__.return_value
    cursor.execute.side_effect = psycopg.Error(
        "database unavailable"
    )

    snapshot = DeploymentDecisionSnapshot(
        deployment_decision_id=10,
        snapshot_date=date(2026, 9, 6),
        recommended_amount=Decimal("25000"),
        actual_amount_deployed=Decimal("10000"),
    )

    with pytest.raises(
        DeploymentDecisionSnapshotRepositoryError,
        match="Failed to create deployment decision snapshot",
    ):
        repository.create(snapshot)

    mock_conn.rollback.assert_called_once()
    mock_conn.commit.assert_not_called()

def test_get_by_id_returns_deployment_decision_snapshot(
    repository,
    mock_conn,
):
    cursor = mock_conn.cursor.return_value.__enter__.return_value

    cursor.fetchone.return_value = (
        123,
        10,
        date(2026, 9, 6),
        Decimal("25000"),
        Decimal("10000"),
    )

    result = repository.get_by_id(123)

    assert isinstance(result, DeploymentDecisionSnapshot)
    assert result.deployment_decision_snapshot_id  == 123
    assert result.deployment_decision_id == 10
    assert result.snapshot_date == date(2026, 9, 6)
    assert result.recommended_amount == Decimal("25000")
    assert result.actual_amount_deployed == Decimal("10000")

    sql, params = cursor.execute.call_args.args

    assert "SELECT" in sql
    assert (
        "FROM cycleguard.deployment_decision_snapshot"
        in sql
    )
    assert "WHERE deployment_decision_snapshot_id  = %s" in sql
    assert params == (123,)


def test_get_by_id_returns_none_when_missing(
    repository,
    mock_conn,
):
    cursor = mock_conn.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = None

    result = repository.get_by_id(999)

    assert result is None
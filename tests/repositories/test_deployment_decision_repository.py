from decimal import Decimal
from unittest.mock import MagicMock

import psycopg
import pytest

from models.deployment_decision import DeploymentDecision
from repositories.deployment_decision_repository import (
    DeploymentDecisionRepository,
    DeploymentDecisionRepositoryError,
)


@pytest.fixture
def mock_conn():
    return MagicMock()


@pytest.fixture
def repository(mock_conn):
    return DeploymentDecisionRepository(mock_conn)


def test_create_deployment_decision(repository, mock_conn):
    cursor = mock_conn.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = (123,)

    decision = DeploymentDecision(
        deployment_decision_id=None,
        account_number="ABC123",
        recommended_amount=Decimal("25000"),
        reason="Favorable market regime and excess defensive allocation.",
    )

    result = repository.create(decision)

    assert result == 123

    cursor.execute.assert_called_once()

    sql, params = cursor.execute.call_args.args

    assert "INSERT INTO cycleguard.deployment_decision" in sql
    assert "SELECT" in sql
    assert "FROM cycleguard.accounts" in sql
    assert "WHERE account_number = %s" in sql
    assert "RETURNING id" in sql

    assert params == (
        Decimal("25000"),
        "Favorable market regime and excess defensive allocation.",
        "ABC123",
    )

    mock_conn.commit.assert_called_once()
    mock_conn.rollback.assert_not_called()


def test_create_deployment_decision_account_not_found(
    repository,
    mock_conn,
):
    cursor = mock_conn.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = None

    decision = DeploymentDecision(
        account_number="MISSING",
        recommended_amount=Decimal("25000"),
        reason="Favorable market conditions.",
    )

    with pytest.raises(
        DeploymentDecisionRepositoryError,
        match="Account not found: MISSING",
    ):
        repository.create(decision)

    mock_conn.rollback.assert_called_once()
    mock_conn.commit.assert_not_called()


def test_create_deployment_decision_database_error(
    repository,
    mock_conn,
):
    cursor = mock_conn.cursor.return_value.__enter__.return_value
    cursor.execute.side_effect = psycopg.Error(
        "database unavailable"
    )

    decision = DeploymentDecision(
        account_number="ABC123",
        recommended_amount=Decimal("25000"),
        reason="Favorable market conditions.",
    )

    with pytest.raises(
        DeploymentDecisionRepositoryError,
        match="Failed to insert deployment decision",
    ):
        repository.create(decision)

    mock_conn.rollback.assert_called_once()
    mock_conn.commit.assert_not_called()

def test_get_by_id_returns_deployment_decision(
    repository,
    mock_conn,
):
    cursor = mock_conn.cursor.return_value.__enter__.return_value

    cursor.fetchone.return_value = (
        123,
        "ABC123",
        Decimal("25000"),
        "Favorable market conditions.",
    )

    result = repository.get_by_id(123)

    assert isinstance(result, DeploymentDecision)
    assert result.deployment_decision_id == 123
    assert result.account_number == "ABC123"
    assert result.recommended_amount == Decimal("25000")
    assert result.reason == "Favorable market conditions."

    sql, params = cursor.execute.call_args.args

    assert "SELECT" in sql
    assert "FROM cycleguard.deployment_decision" in sql
    assert "JOIN cycleguard.accounts" in sql
    assert "WHERE dd.id = %s" in sql

    assert params == (123,)


def test_get_by_id_returns_none_when_missing(
    repository,
    mock_conn,
):
    cursor = mock_conn.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = None

    result = repository.get_by_id(999)

    assert result is None
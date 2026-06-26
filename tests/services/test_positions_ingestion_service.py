from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from services.positions_ingestion_service import (
    PositionsIngestionService,
)


@pytest.fixture
def service():

    return PositionsIngestionService(
        account_repo=MagicMock(),
        security_repo=MagicMock(),
        snapshot_repo=MagicMock(),
        position_repo=MagicMock(),
        import_history_repo=MagicMock(),
        loader=MagicMock(),
        validator=MagicMock(),
    )


def test_import_type(service):

    assert service.import_type == "positions"


@patch(
    "services.positions_ingestion_service.DBConnection"
)
@patch(
    "services.positions_ingestion_service.AccountRepository"
)
@patch(
    "services.positions_ingestion_service.SecurityRepository"
)
@patch(
    "services.positions_ingestion_service.SnapshotRepository"
)
@patch(
    "services.positions_ingestion_service.PositionRepository"
)
@patch(
    "services.positions_ingestion_service.ImportHistoryRepository"
)
@patch(
    "services.positions_ingestion_service.PositionsCSVLoader"
)
@patch(
    "services.positions_ingestion_service.PositionsValidator"
)
def test_build(
    mock_validator,
    mock_loader,
    mock_import_history_repo,
    mock_position_repo,
    mock_snapshot_repo,
    mock_security_repo,
    mock_account_repo,
    mock_db_connection,
):

    conn = MagicMock()

    mock_db_connection.return_value.connect.return_value = conn

    service = (
        PositionsIngestionService.build()
    )

    assert isinstance(
        service,
        PositionsIngestionService,
    )

    mock_db_connection.return_value.connect.assert_called_once()

    mock_account_repo.assert_called_once_with(conn)
    mock_security_repo.assert_called_once_with(conn)
    mock_snapshot_repo.assert_called_once_with(conn)
    mock_position_repo.assert_called_once_with(conn)
    mock_import_history_repo.assert_called_once_with(conn)

    mock_loader.assert_called_once()
    mock_validator.assert_called_once()


def test_persist_success(service):

    account = SimpleNamespace(id=123)

    service._snapshot_repo.create_snapshot.return_value = 999

    service._security_repo.get_or_create.side_effect = [
        SimpleNamespace(id=1),
        SimpleNamespace(id=2),
    ]

    dataframe = pd.DataFrame(
        [
            {
                "symbol": "AAPL",
                "quantity": 10,
                "market_value": 2000.0,
                "cost_basis": 1500.0,
            },
            {
                "symbol": "MSFT",
                "quantity": 5,
                "market_value": 1500.0,
                "cost_basis": 1000.0,
            },
        ]
    )

    rows = service.persist(
        dataframe=dataframe,
        account=account,
    )

    assert rows == 2

    service._snapshot_repo.create_snapshot.assert_called_once_with(
        account_id=123
    )

    assert (
        service._security_repo.get_or_create.call_count
        == 2
    )

    assert (
        service._position_repo.insert.call_count
        == 2
    )

    service._position_repo.insert.assert_any_call(
        snapshot_id=999,
        security_id=1,
        quantity=10,
        market_value=2000.0,
        cost_basis=1500.0,
    )

    service._position_repo.insert.assert_any_call(
        snapshot_id=999,
        security_id=2,
        quantity=5,
        market_value=1500.0,
        cost_basis=1000.0,
    )


def test_persist_raises_on_insert_error(
    service,
):

    account = SimpleNamespace(id=123)

    service._snapshot_repo.create_snapshot.return_value = 999

    service._security_repo.get_or_create.return_value = (
        SimpleNamespace(id=1)
    )

    service._position_repo.insert.side_effect = (
        Exception("insert failed")
    )

    dataframe = pd.DataFrame(
        [
            {
                "symbol": "AAPL",
                "quantity": 10,
                "market_value": 2000.0,
                "cost_basis": 1500.0,
            }
        ]
    )

    from services.positions_ingestion_service import (
        PositionsIngestionServiceError,
    )

    with pytest.raises(
        PositionsIngestionServiceError,
        match="Unable to import position for symbol 'AAPL'",
    ):
        service.persist(
            dataframe=dataframe,
            account=account,
        )

    service._snapshot_repo.create_snapshot.assert_called_once()
    service._security_repo.get_or_create.assert_called_once()
    service._position_repo.insert.assert_called_once()
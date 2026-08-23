from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from datetime import date

from models.account import Account
from models.snapshot import Snapshot
from models.security import Security

from services.positions_ingestion_service import (
    PositionsIngestionService,
    PositionsIngestionServiceError,
    SnapshotAlreadyExistsError,
)

from database.transaction_manager import TransactionManager


@pytest.fixture
def service():

    return PositionsIngestionService(
        account_repo=MagicMock(),
        security_repo=MagicMock(),
        snapshot_repo=MagicMock(),
        position_repo=MagicMock(),
        import_history_repo=MagicMock(),
        import_audit_service=MagicMock(),
        security_resolution_service=MagicMock(),
        loader=MagicMock(),
        validator=MagicMock(),
        transaction_manager=MagicMock(),
    )


def test_import_type(service):

    assert service.import_type == "positions"


@patch(
    "services.positions_ingestion_service.DBConnection"
)
@patch(
    "services.positions_ingestion_service.TransactionManager"
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
    "services.positions_ingestion_service.SecurityResolutionService"
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
    mock_security_resolution_service,
    mock_import_history_repo,
    mock_position_repo,
    mock_snapshot_repo,
    mock_security_repo,
    mock_account_repo,
    mock_transaction_manager,
    mock_db_connection,
):

    conn = MagicMock()

    mock_db_connection.return_value.connect.return_value = conn

    service = PositionsIngestionService.build()

    mock_transaction_manager.assert_called_once_with(conn)

    assert isinstance(
        service,
        PositionsIngestionService,
    )

    mock_db_connection.return_value.connect.assert_called_once()

    mock_account_repo.assert_called_once_with(conn)
    assert mock_security_repo.call_count == 1
    mock_snapshot_repo.assert_called_once_with(conn)
    mock_position_repo.assert_called_once_with(conn)
    mock_import_history_repo.assert_called_once_with(conn)
    mock_security_repo.assert_called_once_with(conn)

    mock_loader.assert_called_once()
    mock_validator.assert_called_once()


def test_persist_success(service):

    account = SimpleNamespace(id=123, name="Joint WROS TOD")


    #
    # No existing snapshot
    #
    service._snapshot_repo.get_by_account_and_date.return_value = None

    #
    # Snapshot creation
    #
    mock_snapshot = SimpleNamespace(id=999)
    service._snapshot_repo.create.return_value = mock_snapshot

    #
    # Security resolution
    #
    service._security_resolution_service.resolve.side_effect = [
        SimpleNamespace(id=1, symbol="AAPL"),
        SimpleNamespace(id=2, symbol="MSFT"),
    ]

    dataframe = pd.DataFrame(
        [
            {
                "symbol": "AAPL",
                "quantity": 10,
                "average_cost_basis": 150.0,
                "cost_basis_total": 1500.0,
                "current_value": 2000.0,
                "percent_of_account": 0.5,
                "todays_gain_loss_dollar": 10.0,
                "todays_gain_loss_percent": 0.01,
                "total_gain_loss_dollar": 500.0,
                "total_gain_loss_percent": 0.33,
                "description": "Apple Inc",
            },
            {
                "symbol": "MSFT",
                "quantity": 5,
                "average_cost_basis": 200.0,
                "cost_basis_total": 1000.0,
                "current_value": 1500.0,
                "percent_of_account": 0.3,
                "todays_gain_loss_dollar": 20.0,
                "todays_gain_loss_percent": 0.02,
                "total_gain_loss_dollar": 500.0,
                "total_gain_loss_percent": 0.5,
                "description": "Microsoft Corp",
            },
        ]
    )

    rows = service.persist(
        dataframe=dataframe,
        account=account,
        snapshot_date="2025-12-31",
        import_history_id=123,
    )

    assert rows == 2

    # Verify duplicate snapshot check
    service._snapshot_repo.get_by_account_and_date.assert_called_once_with(
        123,
        "2025-12-31",
    )

    # Check snapshot creation call
    snapshot_arg = service._snapshot_repo.create.call_args.args[0]
    assert snapshot_arg.snapshot_date == "2025-12-31"

    # Check security resolution calls
    assert service._security_resolution_service.resolve.call_count == 2

    # Check position insertions
    assert service._position_repo.insert.call_count == 2

    pos1 = service._position_repo.insert.call_args_list[0].args[0]
    assert pos1.account_id == 123
    assert pos1.security_id == 1
    assert pos1.snapshot_id == 999
    assert pos1.quantity == 10

    pos2 = service._position_repo.insert.call_args_list[1].args[0]
    assert pos2.account_id == 123
    assert pos2.security_id == 2
    assert pos2.snapshot_id == 999
    assert pos2.quantity == 5


def test_persist_raises_on_insert_error(
    service,
):

    account = SimpleNamespace(id=123, name="Joint WROS TOD")
    service._snapshot_repo.get_by_account_and_date.return_value = None
    mock_snapshot = SimpleNamespace(id=999)
    service._snapshot_repo.create.return_value = mock_snapshot

    service._security_resolution_service.resolve.return_value = (
        SimpleNamespace(id=1, symbol="AAPL")
    )

    service._position_repo.insert.side_effect = (
        Exception("insert failed")
    )

    dataframe = pd.DataFrame(
        [
            {
                "symbol": "AAPL",
                "quantity": 10,
                "average_cost_basis": 150.0,
                "cost_basis_total": 1500.0,
                "current_value": 2000.0,
                "percent_of_account": 0.5,
                "todays_gain_loss_dollar": 10.0,
                "todays_gain_loss_percent": 0.01,
                "total_gain_loss_dollar": 500.0,
                "total_gain_loss_percent": 0.33,
                "description": "Apple Inc",
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
            snapshot_date="2025-12-31",
            import_history_id=123,
        )

    service._snapshot_repo.create.assert_called_once()
    service._security_resolution_service.resolve.assert_called_once()
    service._position_repo.insert.assert_called_once()

def test_persist_raises_when_snapshot_already_exists(
    service,
):

    account = SimpleNamespace(
        id=123,
        name="Joint WROS TOD",
    )

    service._snapshot_repo.get_by_account_and_date.return_value = (
        SimpleNamespace(id=999)
    )

    dataframe = pd.DataFrame(
        [
            {
                "symbol": "AAPL",
                "quantity": 10,
                "average_cost_basis": 150.0,
                "cost_basis_total": 1500.0,
                "current_value": 2000.0,
                "percent_of_account": 0.5,
                "todays_gain_loss_dollar": 10.0,
                "todays_gain_loss_percent": 0.01,
                "total_gain_loss_dollar": 500.0,
                "total_gain_loss_percent": 0.33,
                "description": "Apple Inc",
            }
        ]
    )

    with pytest.raises(
        SnapshotAlreadyExistsError,
        match="Snapshot already exists",
    ):
        service.persist(
            dataframe=dataframe,
            account=account,
            snapshot_date="2025-12-31",
            import_history_id=123,
        )


def test_positions_import_sets_import_history_id(
    service,
):
    account = SimpleNamespace(
        id=123,
        name="Joint WROS TOD",
    )

    import_history_id = 123

    service._snapshot_repo.get_by_account_and_date.return_value = None

    service._snapshot_repo.create.return_value = Snapshot(
        id=456,
        account_id=account.id,
        snapshot_date="2026-01-01",
        import_history_id=import_history_id,
    )

    service._security_resolution_service.resolve.return_value = Security(
        id=99,
        symbol="AAPL",
        description="Apple Inc",
    )

    dataframe = pd.DataFrame(
        [
            {
                "symbol": "AAPL",
                "description": "Apple Inc",
                "quantity": 10,
                "average_cost_basis": 100,
                "cost_basis_total": 1000,
                "current_value": 1100,
                "percent_of_account": 10,
                "todays_gain_loss_dollar": 10,
                "todays_gain_loss_percent": 1,
                "total_gain_loss_dollar": 100,
                "total_gain_loss_percent": 10,
            }
        ]
    )

    imported = service.persist(
        dataframe=dataframe,
        account=account,
        snapshot_date="2026-01-01",
        import_history_id=import_history_id,
    )

    assert imported == 1

    position = (
        service._position_repo
        .insert
        .call_args
        .args[0]
    )

    assert position.import_history_id == import_history_id

def test_positions_import_creates_snapshot(
    service,
):
    account = SimpleNamespace(
        id=123,
        name="Joint WROS TOD",
    )

    import_history_id = 123
    snapshot_date = "2026-01-01"

    service._snapshot_repo.get_by_account_and_date.return_value = None

    service._snapshot_repo.create.return_value = Snapshot(
        id=456,
        account_id=account.id,
        snapshot_date=snapshot_date,
        import_history_id=import_history_id,
    )

    service._security_resolution_service.resolve.return_value = Security(
        id=99,
        symbol="AAPL",
        description="Apple Inc",
    )

    dataframe = pd.DataFrame(
        [
            {
                "symbol": "AAPL",
                "description": "Apple Inc",
                "quantity": 10,
                "average_cost_basis": 100,
                "cost_basis_total": 1000,
                "current_value": 1100,
                "percent_of_account": 10,
                "todays_gain_loss_dollar": 10,
                "todays_gain_loss_percent": 1,
                "total_gain_loss_dollar": 100,
                "total_gain_loss_percent": 10,
            }
        ]
    )

    imported = service.persist(
        dataframe=dataframe,
        account=account,
        snapshot_date=snapshot_date,
        import_history_id=import_history_id,
    )

    assert imported == 1

    service._snapshot_repo.create.assert_called_once()

    snapshot = (
        service._snapshot_repo
        .create
        .call_args
        .args[0]
    )

    assert snapshot.account_id == account.id
    assert snapshot.snapshot_date == snapshot_date
    assert snapshot.import_history_id == import_history_id

@patch(
    "services.base_ingestion_service.calculate_file_hash",
    return_value="test-file-hash",
)
def test_positions_import_failure_during_persist_raises_error(
    mock_file_hash,
    service,
):
    account = SimpleNamespace(
        id=123,
        name="Joint WROS TOD",
        institution="Fidelity",
        account_number="123456",
    )

    service._account_repo.get_by_name.return_value = account

    service._import_history_repo.exists.return_value = False

    service._import_history_repo.insert.return_value = SimpleNamespace(
        id=123,
        account_id=123,
        import_type="positions",
        status="RUNNING",
    )

    service._loader.load.return_value = pd.DataFrame(
        [
            {
                "symbol": "AAPL",
                "description": "Apple Inc",
                "quantity": 10,
                "average_cost_basis": 100,
                "cost_basis_total": 1000,
                "current_value": 1100,
                "percent_of_account": 10,
                "todays_gain_loss_dollar": 10,
                "todays_gain_loss_percent": 1,
                "total_gain_loss_dollar": 100,
                "total_gain_loss_percent": 10,
            }
        ]
    )

    service._snapshot_repo.get_by_account_and_date.return_value = None

    service._snapshot_repo.create.return_value = Snapshot(
        id=456,
        account_id=123,
        snapshot_date="2026-01-01",
        import_history_id=123,
    )

    service._security_resolution_service.resolve.return_value = Security(
        id=99,
        symbol="AAPL",
        description="Apple Inc",
    )

    service._position_repo.insert.side_effect = Exception(
        "database failure"
    )

    with pytest.raises(
        PositionsIngestionServiceError,
        match="Unable to import position for symbol 'AAPL'",
    ):
        service.ingest(
            csv_file="positions.csv",
            name="Joint WROS TOD",
            snapshot_date="2026-01-01",
        )

    service._position_repo.insert.assert_called_once()

@patch(
    "services.base_ingestion_service.calculate_file_hash",
    return_value="test-file-hash",
)
def test_positions_dry_run_does_not_persist(
    mock_file_hash,
    service,
):
    account = SimpleNamespace(
        id=123,
        name="Joint WROS TOD",
        institution="Fidelity",
        account_number="123456",
    )

    service._account_repo.get_by_name.return_value = account

    service._import_history_repo.exists.return_value = False

    service._loader.load.return_value = pd.DataFrame(
        [
            {
                "symbol": "AAPL",
                "description": "Apple Inc",
                "quantity": 10,
                "average_cost_basis": 100,
                "cost_basis_total": 1000,
                "current_value": 1100,
                "percent_of_account": 10,
                "todays_gain_loss_dollar": 10,
                "todays_gain_loss_percent": 1,
                "total_gain_loss_dollar": 100,
                "total_gain_loss_percent": 10,
            }
        ]
    )

    result = service.ingest(
        csv_file="positions.csv",
        name="Joint WROS TOD",
        snapshot_date="2026-01-01",
        dry_run=True,
    )

    assert result.account_id == 123
    assert result.account_name == "Joint WROS TOD"
    assert result.institution == "Fidelity"
    assert result.import_type == service.import_type
    assert result.filename == "positions.csv"
    assert result.snapshot_date == "2026-01-01"
    assert result.rows_read == 1
    assert result.rows_imported == 0
    assert result.rows_skipped == 0
    assert result.import_history_id is None
    assert result.snapshot_id is None
    assert result.status == "SUCCESS"
    assert result.warnings == []

    service._import_history_repo.insert.assert_not_called()
    service.persist = MagicMock()
    service.persist.assert_not_called()
    service._snapshot_repo.create.assert_not_called()
    service._position_repo.insert.assert_not_called()
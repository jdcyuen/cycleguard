from unittest.mock import MagicMock, patch

from cli.rollback_import import main, parse_args


def make_import_history():
    history = MagicMock()
    history.id = 42
    history.account_id = 1
    history.import_type = "transactions"
    history.institution = "Fidelity"
    history.filename = "Transactions_Apr2026.csv"
    history.file_hash = "abc123"
    history.snapshot_date = "2026-04-30"
    history.status = "SUCCESS"
    return history


@patch("cli.rollback_import.display_result")
@patch("cli.rollback_import.ImportRollbackService")
@patch("cli.rollback_import.TransactionRepository")
@patch("cli.rollback_import.SnapshotRepository")
@patch("cli.rollback_import.PositionRepository")
@patch("cli.rollback_import.ImportHistoryRepository")
@patch("cli.rollback_import.DBConnection")
@patch("cli.rollback_import.parse_args")
def test_main_runs_rollback(
    mock_parse_args,
    mock_db_connection,
    mock_import_history_repo,
    mock_position_repo,
    mock_snapshot_repo,
    mock_transaction_repo,
    mock_rollback_service,
    mock_display_result,
):
    mock_parse_args.return_value = MagicMock(
        import_history_id=42,
        confirm=False,
        delete_import_history=False,
    )

    # Mock database connection
    mock_conn = MagicMock()
    mock_db_connection.return_value.connect.return_value = mock_conn

    # Mock import history lookup
    history = make_import_history()
    mock_import_history_repo.return_value.get_by_id.return_value = history

    # Mock rollback result
    rollback_result = {
        "import_history_id": 42,
        "transactions_deleted": 247,
        "positions_deleted": 0,
        "snapshots_deleted": 0,
    }
    mock_rollback_service.return_value.rollback.return_value = rollback_result

    result = main()

    assert result == 0

    mock_import_history_repo.return_value.get_by_id.assert_called_once_with(42)

    mock_rollback_service.return_value.rollback.assert_called_once_with(
        import_history_id=42,
        delete_import_history=False,
    )

    mock_display_result.assert_called_once_with(rollback_result)

    mock_conn.close.assert_called_once()

@patch("cli.rollback_import.display_result")
@patch("cli.rollback_import.ImportRollbackService")
@patch("cli.rollback_import.TransactionRepository")
@patch("cli.rollback_import.SnapshotRepository")
@patch("cli.rollback_import.PositionRepository")
@patch("cli.rollback_import.ImportHistoryRepository")
@patch("cli.rollback_import.DBConnection")
@patch("cli.rollback_import.parse_args")
def test_rollback_keeps_import_history_by_default(
    mock_parse_args,
    mock_db_connection,
    mock_import_history_repo,
    mock_position_repo,
    mock_snapshot_repo,
    mock_transaction_repo,
    mock_rollback_service,
    mock_display_result,
):
    mock_parse_args.return_value = MagicMock(
        import_history_id=42,
        confirm=False,
        delete_import_history=False,
    )

    mock_conn = MagicMock()
    mock_db_connection.return_value.connect.return_value = mock_conn

    history = make_import_history()
    mock_import_history_repo.return_value.get_by_id.return_value = history

    rollback_result = {
        "import_history_id": 42,
        "transactions_deleted": 247,
        "positions_deleted": 0,
        "snapshots_deleted": 0,
        "import_history_deleted": 0,
    }

    mock_rollback_service.return_value.rollback.return_value = (
        rollback_result
    )

    result = main()

    assert result == 0

    mock_rollback_service.return_value.rollback.assert_called_once_with(
        import_history_id=42,
        delete_import_history=False,
    )

    mock_display_result.assert_called_once_with(rollback_result)

    mock_conn.close.assert_called_once()  


@patch("cli.rollback_import.display_result")
@patch("cli.rollback_import.ImportRollbackService")
@patch("cli.rollback_import.TransactionRepository")
@patch("cli.rollback_import.SnapshotRepository")
@patch("cli.rollback_import.PositionRepository")
@patch("cli.rollback_import.ImportHistoryRepository")
@patch("cli.rollback_import.DBConnection")
@patch("cli.rollback_import.parse_args")
def test_main_passes_delete_import_history_flag(
    mock_parse_args,
    mock_db_connection,
    mock_import_history_repo,
    mock_position_repo,
    mock_snapshot_repo,
    mock_transaction_repo,
    mock_rollback_service,
    mock_display_result,
):
    mock_parse_args.return_value = MagicMock(
        import_history_id=42,
        confirm=False,
        delete_import_history=True,
    )

    mock_conn = MagicMock()
    mock_db_connection.return_value.connect.return_value = mock_conn

    history = make_import_history()
    mock_import_history_repo.return_value.get_by_id.return_value = history

    rollback_result = {
        "import_history_id": 42,
        "transactions_deleted": 247,
        "positions_deleted": 0,
        "snapshots_deleted": 0,
        "import_history_deleted": 1,
    }

    mock_rollback_service.return_value.rollback.return_value = rollback_result

    result = main()

    assert result == 0

    mock_rollback_service.return_value.rollback.assert_called_once_with(
        import_history_id=42,
        delete_import_history=True,
    )

    mock_conn.close.assert_called_once() 

def test_parse_args_accepts_delete_import_history(monkeypatch):
    monkeypatch.setattr(
        "sys.argv",
        [
            "rollback_import.py",
            "--import-history-id",
            "42",
            "--delete-import-history",
        ],
    )

    args = parse_args()

    assert args.import_history_id == 42
    assert args.delete_import_history is True
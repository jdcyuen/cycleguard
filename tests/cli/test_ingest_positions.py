from unittest.mock import MagicMock, Mock, patch

import pytest

from cli.ingest_positions import main


@patch("cli.ingest_positions.display_results")
@patch("cli.ingest_positions.PositionsIngestionService.build")
@patch("cli.ingest_positions.resolve_snapshot_date")
@patch("cli.ingest_positions.resolve_account")
@patch("cli.ingest_positions.parse_args")
def test_main_runs_ingestion(
    mock_parse_args,
    mock_resolve_account,
    mock_resolve_snapshot_date,
    mock_build,
    mock_display_results,
):
    mock_parse_args.return_value = MagicMock(
        file="positions.csv",
        account="ROLLOVER",
        snapshot_date=None,
        confirm=False,
        dry_run=False,
    )

    mock_resolve_account.return_value = "ROLLOVER"
    mock_resolve_snapshot_date.return_value = "2025-12-31"

    mock_service = Mock()
    mock_service.account_repo = Mock()
    mock_service.ingest.return_value = {
        "inserted": 10,
        "updated": 0,
        "skipped": 0,
    }

    mock_build.return_value = mock_service

    main()

    mock_build.assert_called_once()

    mock_resolve_account.assert_called_once_with(
        account_name="ROLLOVER",
        account_repo=mock_service.account_repo,
    )

    mock_resolve_snapshot_date.assert_called_once_with(
        filename="positions.csv",
        cli_snapshot_date=None,
    )

    mock_service.ingest.assert_called_once_with(
        csv_file="positions.csv",
        name="ROLLOVER",
        snapshot_date="2025-12-31",
        dry_run=False,
    )

    mock_display_results.assert_called_once_with(
        {
            "inserted": 10,
            "updated": 0,
            "skipped": 0,
        },
    )


@patch("cli.ingest_positions.confirm_import")
@patch("cli.ingest_positions.PositionsIngestionService.build")
@patch("cli.ingest_positions.resolve_snapshot_date")
@patch("cli.ingest_positions.resolve_account")
@patch("cli.ingest_positions.parse_args")
def test_main_cancelled_by_user(
    mock_parse_args,
    mock_resolve_account,
    mock_resolve_snapshot_date,
    mock_build,
    mock_confirm_import,
):
    mock_parse_args.return_value = MagicMock(
        file="positions.csv",
        account="ROLLOVER",
        snapshot_date=None,
        confirm=True,
    )

    mock_resolve_account.return_value = "ROLLOVER"
    mock_resolve_snapshot_date.return_value = "2025-12-31"
    mock_confirm_import.return_value = False

    mock_service = Mock()
    mock_service.account_repo = Mock()

    mock_build.return_value = mock_service

    main()

    mock_confirm_import.assert_called_once_with(
        "positions",
        "ROLLOVER",
    )

    mock_service.ingest.assert_not_called()


@patch("cli.ingest_positions.PositionsIngestionService.build")
@patch("cli.ingest_positions.resolve_snapshot_date")
@patch("cli.ingest_positions.resolve_account")
@patch("cli.ingest_positions.parse_args")
def test_main_handles_exception(
    mock_parse_args,
    mock_resolve_account,
    mock_resolve_snapshot_date,
    mock_build,
):
    mock_parse_args.return_value = MagicMock(
        file="positions.csv",
        account="ROLLOVER",
        snapshot_date=None,
        confirm=False,
    )

    mock_resolve_account.return_value = "ROLLOVER"
    mock_resolve_snapshot_date.return_value = "2025-12-31"

    mock_service = Mock()
    mock_service.account_repo = Mock()
    mock_service.ingest.side_effect = Exception("database error")

    mock_build.return_value = mock_service

    with pytest.raises(SystemExit) as excinfo:
        main()

    assert excinfo.value.code == 1
from unittest.mock import MagicMock, patch

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
    )

    mock_resolve_account.return_value = "ROLLOVER"

    mock_resolve_snapshot_date.return_value = "2025-12-31"

    mock_service = MagicMock()

    mock_service.ingest.return_value = {
        "inserted": 10,
        "updated": 0,
        "skipped": 0,
    }

    mock_build.return_value = mock_service

    main()

    mock_resolve_account.assert_called_once_with(
        "ROLLOVER"
    )

    mock_resolve_snapshot_date.assert_called_once_with(
        snapshot_date=None,
        csv_file="positions.csv",
    )

    mock_build.assert_called_once()

    mock_service.ingest.assert_called_once_with(
        csv_file="positions.csv",
        account_name="ROLLOVER",
        snapshot_date="2025-12-31",
    )

    mock_display_results.assert_called_once_with(
        "ROLLOVER",
        {
            "inserted": 10,
            "updated": 0,
            "skipped": 0,
        },
    )


@patch("cli.ingest_positions.confirm_import")
@patch("cli.ingest_positions.parse_args")
def test_main_cancelled_by_user(
    mock_parse_args,
    mock_confirm_import,
):

    mock_parse_args.return_value = MagicMock(
        file="positions.csv",
        account="ROLLOVER",
        snapshot_date=None,
        confirm=True,
    )

    mock_confirm_import.return_value = False

    with patch(
        "cli.ingest_positions.resolve_account",
        return_value="ROLLOVER",
    ):
        with patch(
            "cli.ingest_positions.resolve_snapshot_date",
            return_value="2025-12-31",
        ):
            main()

    mock_confirm_import.assert_called_once_with(
        "positions",
        "ROLLOVER",
    )


@patch("cli.ingest_positions.print")
@patch("cli.ingest_positions.PositionsIngestionService.build")
@patch("cli.ingest_positions.resolve_snapshot_date")
@patch("cli.ingest_positions.resolve_account")
@patch("cli.ingest_positions.parse_args")
def test_main_handles_exception(
    mock_parse_args,
    mock_resolve_account,
    mock_resolve_snapshot_date,
    mock_build,
    mock_print,
):

    mock_parse_args.return_value = MagicMock(
        file="positions.csv",
        account="ROLLOVER",
        snapshot_date=None,
        confirm=False,
    )

    mock_resolve_account.return_value = "ROLLOVER"

    mock_resolve_snapshot_date.return_value = "2025-12-31"

    mock_service = MagicMock()

    mock_service.ingest.side_effect = Exception(
        "database error"
    )

    mock_build.return_value = mock_service

    try:
        main()
        assert False, "Expected SystemExit"
    except SystemExit as exc:
        assert exc.code == 1

    mock_print.assert_any_call(
        "Positions import failed: database error"
    )
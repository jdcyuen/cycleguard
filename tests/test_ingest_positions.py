from unittest.mock import MagicMock, patch

from src.cli.ingest_positions import resolve_snapshot_date, main


# --------------------------------------------------
# Snapshot date resolution tests
# --------------------------------------------------


def test_resolve_snapshot_date_from_cli_arg():

    result = resolve_snapshot_date(
        snapshot_date_arg="2026-01-15", file_path="portfolio.csv"
    )

    assert result == "2026-01-15"


def test_resolve_snapshot_date_from_filename():

    result = resolve_snapshot_date(
        snapshot_date_arg=None, file_path="Portfolio_Positions_Jan_15_2026.csv"
    )

    assert result == "2026-01-15"


def test_resolve_snapshot_date_fallback_to_today():

    result = resolve_snapshot_date(snapshot_date_arg=None, file_path="portfolio.csv")

    # only validate format
    assert len(result) == 10
    assert result.count("-") == 2


# --------------------------------------------------
# CLI orchestration test
# --------------------------------------------------


@patch("src.cli.ingest_positions.build_service")
@patch(
    "sys.argv",
    ["ingest_positions", "--file", "Portfolio_Positions_Jan_15_2026.csv", "--confirm"],
)
def test_main_runs_ingestion(mock_build_service):

    # ----------------------------------------------
    # Mock ingestion service
    # ----------------------------------------------
    mock_service = MagicMock()

    mock_service.run.return_value = {
        "status": "success",
        "snapshot_id": 1,
        "snapshot_date": "2026-01-15",
        "rows_processed": 2,
    }

    mock_build_service.return_value = mock_service

    # ----------------------------------------------
    # Execute CLI
    # ----------------------------------------------
    main()

    # ----------------------------------------------
    # Validate ingestion executed
    # ----------------------------------------------
    mock_service.run.assert_called_once()

    # ----------------------------------------------
    # Validate arguments passed to service
    # ----------------------------------------------
    kwargs = mock_service.run.call_args.kwargs

    assert kwargs["file_path"] == ("Portfolio_Positions_Jan_15_2026.csv")

    assert kwargs["snapshot_date"] == "2026-01-15"

    assert kwargs["confirm"] is True

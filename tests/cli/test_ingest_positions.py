from argparse import Namespace
from unittest.mock import Mock
from unittest.mock import patch

from cli.ingest_positions import main


@patch("cli.ingest_positions.parse_args")
@patch("cli.ingest_positions.resolve_account")
@patch("cli.ingest_positions.PositionsIngestionService")
def test_ingest_positions_success(mock_service_class, mock_resolve_account,mock_parse_args,):

    mock_parse_args.return_value = Namespace(
        file="positions.csv",
        account="rollover_ira",
        snapshot_date=None,
        confirm=False,
    )

    mock_resolve_account.return_value = "rollover_ira"

    mock_service = Mock()

    mock_service.ingest.return_value = (
        Mock(
            rows_imported=42,
            account_name="rollover_ira",
            import_type="positions",
            file_name="positions.csv",
        )
    )

    mock_service_class.build.return_value = (mock_service)

    args = [
        "--file",
        "positions.csv",
        "--account",
        "rollover_ira",
    ]

    main()

    mock_service.ingest.assert_called_once()
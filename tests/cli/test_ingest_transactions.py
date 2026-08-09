from argparse import Namespace
from unittest.mock import Mock
from unittest.mock import patch

from cli.ingest_transactions import (
    main,
)

from argparse import Namespace
from unittest.mock import Mock, patch

from cli.ingest_transactions import main


@patch("cli.ingest_transactions.display_results")
@patch("cli.ingest_transactions.parse_args")
@patch("cli.ingest_transactions.resolve_account")
@patch("cli.ingest_transactions.TransactionsIngestionService")
def test_ingest_transactions_success(
    mock_service_class,
    mock_resolve_account,
    mock_parse_args,
    mock_display_results,
):
    # Arrange
    mock_parse_args.return_value = Namespace(
        file="transactions.csv",
        account="rollover_ira",
        confirm=False,
        dry_run=False,
    )

    mock_resolve_account.return_value = "rollover_ira"

    mock_result = Mock(
        rows_imported=100,
        account_name="rollover_ira",
        import_type="transactions",
        filename="transactions.csv",
        snapshot_date=None,
        rows_read=100,
        rows_skipped=0,
        import_history_id=1,
        snapshot_id=None,
        elapsed_ms=125,
    )

    mock_service = Mock()
    mock_service.account_repo = Mock()
    mock_service.ingest.return_value = mock_result

    mock_service_class.build.return_value = mock_service

    # Act
    main()

    # Assert
    mock_service_class.build.assert_called_once()

    mock_resolve_account.assert_called_once_with(
        account_name="rollover_ira",
        account_repo=mock_service.account_repo,
    )

    mock_service.ingest.assert_called_once_with(
        csv_file="transactions.csv",
        name="rollover_ira",
        dry_run=False,
    )

    mock_display_results.assert_called_once_with(mock_result)
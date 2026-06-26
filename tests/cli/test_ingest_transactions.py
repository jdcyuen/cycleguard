from argparse import Namespace
from unittest.mock import Mock
from unittest.mock import patch

from src.cli.ingest_transactions import (
    main,
)


@patch(
    "src.cli.ingest_transactions.parse_args"
)
@patch(
    "src.cli.ingest_transactions.resolve_account"
)
@patch(
    "src.cli.ingest_transactions.TransactionsIngestionService"
)
def test_ingest_transactions_success(
    mock_service_class,
    mock_resolve_account,
    mock_parse_args,
):

    mock_parse_args.return_value = Namespace(
        file="transactions.csv",
        account="rollover_ira",
        confirm=False,
    )

    mock_resolve_account.return_value = (
        "rollover_ira"
    )

    mock_service = Mock()

    mock_service.ingest.return_value = (
        Mock(
            rows_imported=100,
            account_name="rollover_ira",
            import_type="transactions",
            file_name="transactions.csv",
        )
    )

    mock_service_class.build.return_value = (
        mock_service
    )

    main()

    mock_service.ingest.assert_called_once_with(
        csv_file="transactions.csv",
        account_name="rollover_ira",
    )
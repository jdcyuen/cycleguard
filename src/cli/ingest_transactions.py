import argparse

from ingestion.common.cli_ingest_helper import (
    confirm_import,
    display_results,
    resolve_account,
)

from services.transactions_ingestion_service import (
    TransactionsIngestionService,
)


def parse_args():

    parser = argparse.ArgumentParser(
        description="Import Fidelity transactions CSV."
    )

    parser.add_argument(
        "--file",
        required=True,
        help="Transactions CSV file."
    )

    parser.add_argument(
        "--account",
        required=False,
        help="Configured account name."
    )

    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Prompt before importing."
    )

    return parser.parse_args()


def main():

    args = parse_args()

    account_name = resolve_account(args.account)

    if args.confirm:

        if not confirm_import("transactions", account_name):
            print("Import cancelled.")
            return

    service = TransactionsIngestionService.build()

    result = service.ingest(
        csv_file=args.file,
        account_name=account_name,
    )

    display_results(
        account_name,
        result,
    )


if __name__ == "__main__":
    main()
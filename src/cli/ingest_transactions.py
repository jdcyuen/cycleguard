import argparse

from core.logger import get_logger, setup_logging       

from ingestion.common.cli_ingestion_helper import (
    confirm_import,
    display_results,
    resolve_account,
)

from services.transactions_ingestion_service import (
    TransactionsIngestionService,
)


logger = get_logger(__name__)


def parse_args():

    parser = argparse.ArgumentParser(
        description="Import Fidelity transactions CSV."
    )

    parser.add_argument(
        "--file",
        required=True,
        help="Transactions CSV file.",
    )

    parser.add_argument(
        "--account",
        required=False,
        help="Configured account name.",
    )

    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Prompt before importing.",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate the import without writing to the database.",
    )

    return parser.parse_args()


def main():

    setup_logging()
    logger.info("Starting transactions import CLI.")

    args = parse_args()

    logger.info(f"CSV file: {args.file}")

    logger.info(
        f"Requested account: "
        f"{args.account or '<prompt>'}"
)

    logger.debug("Building TransactionsIngestionService.")

    service = TransactionsIngestionService.build()

    logger.info("Resolving account.")
    account_name = resolve_account(account_name=args.account, account_repo=service.account_repo)
    logger.info(f"Using account '{account_name}'.")

    if args.confirm:

        logger.info("Waiting for user confirmation.")

        if not confirm_import("transactions", account_name):
            logger.info("Transactions import cancelled by user.")
            print("Import cancelled.")
            return

    try:

        logger.info("Starting transactions ingestion.")

        result = service.ingest(csv_file=args.file, name=account_name, dry_run=args.dry_run)

        display_results(result)
        logger.info("Transactions import CLI completed successfully.")

    except Exception:
        logger.exception("Transactions import failed.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
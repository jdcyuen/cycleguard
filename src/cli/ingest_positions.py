#src/cli/ingest_positions.py

import argparse
import sys

from core.logger import get_logger, setup_logging  

from ingestion.common.cli_ingestion_helper import (
    confirm_import,
    display_results,
    resolve_account,
    resolve_snapshot_date,
)

from services.positions_ingestion_service import (
    PositionsIngestionService,
    PositionsIngestionServiceError,
    SnapshotAlreadyExistsError,
)

logger = get_logger(__name__)


def parse_args():

    parser = argparse.ArgumentParser(
        description="Import Fidelity positions CSV."
    )

    parser.add_argument(
        "--file",
        required=True,
        help="Positions CSV file.",
    )

    parser.add_argument(
        "--account",
        required=False,
        help="Configured account name.",
    )

    parser.add_argument(
        "--snapshot-date",
        required=False,
        help=(
            "Snapshot date (YYYY-MM-DD). "
            "Defaults to filename or today's date."
        ),
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

    logger.info("Starting positions import CLI.")

    args = parse_args()

    logger.info(f"CSV file: {args.file}")

    logger.info(
        f"Requested account: "
        f"{args.account or '<prompt>'}"
    )

    logger.info(
        f"Requested snapshot date: "
        f"{args.snapshot_date or '<auto>'}"
    )

    logger.debug("Building PositionsIngestionService.")

    service = PositionsIngestionService.build()

    logger.info("Resolving account.")
    account_name = resolve_account(account_name=args.account, account_repo=service.account_repo)
    logger.info(f"Using account '{account_name}'.")

    logger.info("Resolving snapshot date.")
    snapshot_date = resolve_snapshot_date(filename=args.file, cli_snapshot_date=args.snapshot_date)
    logger.info(f"Using snapshot date {snapshot_date}.")

    if args.confirm:

        logger.info("Waiting for user confirmation.")

        if not confirm_import("positions", account_name):
            logger.info("Positions import cancelled by user.")
            print("Import cancelled.")
            return

    try:

        logger.info("Starting positions ingestion.")

        result = service.ingest(csv_file=args.file, name=account_name, snapshot_date=snapshot_date, dry_run=args.dry_run)

        display_results(result)
        logger.info("Positions import CLI completed successfully.")

    except SnapshotAlreadyExistsError as exc:
        logger.warning(str(exc))
        sys.exit(1)

    except PositionsIngestionServiceError as exc:
        logger.error(str(exc))
        sys.exit(1)
    
    except Exception as exc:
        logger.exception("Unexpected error during positions import: %s", exc)
        sys.exit(1)

if __name__ == "__main__":
    main()
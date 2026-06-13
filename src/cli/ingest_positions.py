import argparse
import re
from datetime import datetime, date
from pathlib import Path

from src.database.connection import DBConnection

from src.repositories.account_repo import AccountRepository
from src.repositories.position_repo import PositionRepository
from src.repositories.security_repo import SecurityRepository
from src.repositories.snapshot_repo import SnapshotRepository

from src.ingestion.positions.positions_csv_loader import CSVLoader
from src.ingestion.positions.positions_ingestion_service import IngestionService

from src.core.logger import setup_logging, get_logger


# --------------------------------------------------
# Logging setup
# --------------------------------------------------
setup_logging()

logger = get_logger(__name__)


# --------------------------------------------------
# Snapshot date resolver
# --------------------------------------------------
def resolve_snapshot_date(snapshot_date_arg: str, file_path: str) -> str:
    """
    Resolution priority:

    1. CLI argument
    2. Filename parsing
    3. Current date fallback
    """

    # ----------------------------------------------
    # 1. Explicit CLI snapshot date
    # ----------------------------------------------
    if snapshot_date_arg:
        logger.info(f"Using snapshot date from CLI argument: {snapshot_date_arg}")
        return snapshot_date_arg

    # ----------------------------------------------
    # 2. Derive from filename
    # Example:
    # Portfolio_Positions_Jan_15_2026.csv
    # ----------------------------------------------
    filename = Path(file_path).name

    match = re.search(
        r"Portfolio_Positions_([A-Za-z]{3,9})_(\d{1,2})_(\d{4})", filename
    )

    if match:
        month_str, day, year = match.groups()

        for fmt in ("%b %d %Y", "%B %d %Y"):
            try:
                parsed = datetime.strptime(f"{month_str} {day} {year}", fmt)

                resolved = parsed.date().isoformat()

                logger.info(f"Derived snapshot date from filename: {resolved}")

                return resolved

            except ValueError:
                continue

    # ----------------------------------------------
    # 3. Fallback to current date
    # ----------------------------------------------
    today = date.today().isoformat()

    logger.warning(
        f"Could not derive snapshot date from filename. Using current date: {today}"
    )

    return today


# --------------------------------------------------
# Dependency wiring
# --------------------------------------------------
def build_service():

    conn = DBConnection().connect()

    return IngestionService(
        snapshot_repo=SnapshotRepository(conn),
        account_repo=AccountRepository(conn),
        security_repo=SecurityRepository(conn),
        position_repo=PositionRepository(conn),
        loader=CSVLoader(),
    )


# --------------------------------------------------
# CLI entry point
# --------------------------------------------------
def main():

    parser = argparse.ArgumentParser(
        description="CycleGuard portfolio ingestion pipeline"
    )

    parser.add_argument("--file", required=True, help="Path to portfolio CSV file")

    parser.add_argument(
        "--snapshot-date", required=False, help="Explicit snapshot date (YYYY-MM-DD)"
    )

    parser.add_argument(
        "--confirm", action="store_true", help="Skip confirmation prompt"
    )

    args = parser.parse_args()

    # ----------------------------------------------
    # Resolve snapshot date
    # ----------------------------------------------
    snapshot_date = resolve_snapshot_date(
        snapshot_date_arg=args.snapshot_date, file_path=args.file
    )

    print("\n--- CycleGuard Ingestion ---")
    print(f"File: {args.file}")
    print(f"Snapshot Date: {snapshot_date}")

    logger.info(f"CSV file: {args.file}")
    logger.info(f"Resolved snapshot date: {snapshot_date}")

    # ----------------------------------------------
    # Confirmation gate
    # ----------------------------------------------
    if not args.confirm:
        confirm = input("\nProceed with ingestion? (y/n): ")

        if confirm.lower() != "y":
            logger.warning("Ingestion aborted by user")
            print("Aborted.")
            return

        confirmed = True

    else:
        confirmed = True
        logger.info("Confirmed via --confirm flag")

    # ----------------------------------------------
    # Build ingestion service
    # ----------------------------------------------
    service = build_service()

    # ----------------------------------------------
    # Execute ingestion
    # ----------------------------------------------
    result = service.run(
        file_path=args.file, snapshot_date=snapshot_date, confirm=confirmed
    )

    # ----------------------------------------------
    # Success output
    # ----------------------------------------------
    print("\n--- Ingestion Complete ---")
    print(f"Snapshot ID: {result['snapshot_id']}")
    print(f"Rows Processed: {result['rows_processed']}")

    logger.info(
        f"Ingestion successful. "
        f"snapshot_id={result['snapshot_id']}, "
        f"rows_processed={result['rows_processed']}"
    )


if __name__ == "__main__":
    main()

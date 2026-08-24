import argparse
import sys

from core.logger import get_logger, setup_logging 

from repositories.import_history_repo import (
    ImportHistoryRepository,
)
from repositories.position_repo import PositionRepository
from repositories.snapshot_repo import SnapshotRepository
from repositories.transaction_repo import TransactionRepository

from services.import_rollback_service import (
    ImportRollbackService,
)

from database.connection import DBConnection
from database.transaction_manager import TransactionManager

logger = get_logger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(
    description="Rollback a CycleGuard import."
    )

    parser.add_argument(
        "--import-history-id",
        type=int,
        required=True,
        help="ID of the import history record to rollback.",
    )

    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Prompt for confirmation before performing rollback.",
    )

    parser.add_argument(
        "--delete-import-history",
        action="store_true",
        help="Delete the import_history record in addition to the other data.",
    )

    return parser.parse_args()


def confirm_rollback(import_history) -> bool:
    """
    Ask the user to confirm the rollback.
    """

    print()
    print("=" * 60)
    print("IMPORT ROLLBACK")
    print("=" * 60)
    print()
    print(f"Import History ID : {import_history.id}")
    print(f"Account ID        : {import_history.account_id}")
    print(f"Import Type       : {import_history.import_type}")
    print(f"Institution       : {import_history.institution}")
    print(f"Filename          : {import_history.filename}")
    print(f"File Hash         : {import_history.file_hash}")
    print(f"Snapshot Date     : {import_history.snapshot_date}")
    print(f"Status            : {import_history.status}")
    print()

    answer = input(
        "Are you sure you want to rollback this import? (y/n): "
    ).strip().lower()

    confirmed = answer in ("y", "yes")

    if confirmed:
        logger.info(
            "User confirmed rollback for import_history_id=%s",
            import_history.id,
        )
    else:
        logger.info(
            "User cancelled rollback for import_history_id=%s",
            import_history.id,
        )

    return confirmed


def display_result(result: dict) -> None:

    """
    Display rollback results.
    """

    print()
    print("=" * 60)
    print("ROLLBACK COMPLETE")
    print("=" * 60)
    print()
    print(
        f"Import History ID       : "
        f"{result['import_history_id']}"
    )
    print(
        f"Transactions Deleted    : "
        f"{result['transactions_deleted']}"
    )
    print(
        f"Positions Deleted       : "
        f"{result['positions_deleted']}"
    )
    print(
        f"Snapshots Deleted       : "
        f"{result['snapshots_deleted']}"
    )
    print()


def main():
    setup_logging()

    logger.info("Starting import rollback CLI.")

    args = parse_args()

    logger.info(
        "Requested rollback: import_history_id=%s",
        args.import_history_id,
    )

    #
    # Build database connection.
    #
    # Use the same database connection/factory
    # used by the other CycleGuard CLIs.
    #
    conn = DBConnection().connect()

    try:

        # Build repositories.
        import_history_repo = ImportHistoryRepository(conn)
        position_repo = PositionRepository(conn)
        snapshot_repo = SnapshotRepository(conn)
        transaction_repo = TransactionRepository(conn)

        # Build rollback service.
        transaction_manager = TransactionManager(conn)
        service = ImportRollbackService(
            transaction_manager=transaction_manager,
            import_history_repo=import_history_repo,
            position_repo=position_repo,
            snapshot_repo=snapshot_repo,
            transaction_repo=transaction_repo,
        )

        #
        # Retrieve import history before asking for confirmation.
        #
        import_history = import_history_repo.get_by_id(args.import_history_id)

        if import_history is None:

            logger.error(
                "Import history ID %s does not exist.",
                args.import_history_id,
            )

            print(
                f"Import history ID "
                f"{args.import_history_id} "
                f"does not exist."
            )

            return 1

        #
        # Confirmation.
        #
        # --confirm means the CLI should ask.
        #
        if args.confirm:

            if not confirm_rollback(import_history):
                print("Rollback cancelled.")
                return 0

        #
        # Perform rollback.
        #
        logger.info(
            "Executing rollback for import_history_id=%s",
            args.import_history_id,
        )

        result = service.rollback(
            import_history_id=args.import_history_id,
            delete_import_history=args.delete_import_history,
        )

        display_result(result)

        logger.info(
            "Import rollback completed successfully: "
            "import_history_id=%s",
            args.import_history_id,
        )

        return 0

    except Exception:

        logger.exception(
            "Import rollback failed: "
            "import_history_id=%s",
            args.import_history_id,
        )

        print(
        "Rollback failed. See the log for details.")

        return 1

    finally:

        conn.close()


if __name__ == "__main__":
    main()

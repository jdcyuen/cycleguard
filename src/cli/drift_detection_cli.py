
"""
CLI: Database-Driven Drift Detection
====================================

PURPOSE
-------
Evaluate the latest stored database snapshot for a configured account.

USAGE
-----
python -m cli.drift_detection
python -m cli.drift_detection --account "Rollover IRA"
python -m cli.drift_detection --list-accounts

ARCHITECTURE
------------
Uses DriftDetectionOrchestrationService so the CLI, standalone dashboard,
and main dashboard share account matching and drift evaluation behavior.

DATA SAFETY
-----------
Read-only workflow. Does not import positions, create snapshots, synchronize
Fidelity data, persist proposals, or execute trades.
"""

import argparse
import json
import sys

from core.logger import get_logger, setup_logging
from database.connection import DBConnection
from repositories.account_repo import AccountRepository
from repositories.snapshot_repo import SnapshotRepository
from services.account_reconciliation_service import (
    AccountReconciliationService,
    AccountReconciliationServiceError,
)
from services.drift_detection_orchestration_service import (
    DriftDetectionOrchestrationService,
)

logger = get_logger(__name__)


def parse_args():
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Evaluate portfolio drift from the latest stored snapshot."
    )
    parser.add_argument(
        "--account",
        help="Configured account name. Prompts for selection when omitted.",
    )
    parser.add_argument(
        "--list-accounts",
        action="store_true",
        help="List matched database/YAML accounts without evaluating drift.",
    )
    return parser.parse_args()


def display_accounts(matches):
    """Print matched database and YAML account names."""
    for index, (database_account, account_config) in enumerate(matches, start=1):
        database_name = getattr(database_account, "name", "<unnamed>")
        config_name = getattr(account_config, "name", "<unnamed>")
        print(f"{index}. {config_name} (database: {database_name})")


def select_account(matches, requested_name=None):
    """Select an account by name or prompt the user."""
    if not matches:
        raise ValueError(
            "No database accounts match the configured YAML account numbers."
        )

    if requested_name:
        requested = requested_name.strip().casefold()
        selected = [
            match
            for match in matches
            if requested
            in {
                str(getattr(match[0], "name", "")).strip().casefold(),
                str(getattr(match[1], "name", "")).strip().casefold(),
            }
        ]

        if len(selected) == 1:
            return selected[0]

        if len(selected) > 1:
            raise ValueError(
                f"Account name {requested_name!r} is ambiguous. "
                "Use an unambiguous configured account name."
            )

        available = ", ".join(
            str(getattr(config, "name", "<unnamed>"))
            for _, config in matches
        )
        raise ValueError(
            f"Account {requested_name!r} was not found. "
            f"Configured accounts: {available}"
        )

    display_accounts(matches)
    while True:
        choice = input("Select account number: ").strip()
        try:
            index = int(choice)
        except ValueError:
            print("Enter the number beside the account.")
            continue

        if 1 <= index <= len(matches):
            return matches[index - 1]

        print(f"Enter a number from 1 to {len(matches)}.")


def main():
    """Run read-only drift detection."""
    setup_logging()
    args = parse_args()

    try:
        with DBConnection() as connection:
            account_repository = AccountRepository(connection)
            snapshot_repository = SnapshotRepository(connection)

            service = DriftDetectionOrchestrationService(
                connection,
                account_repository,
                snapshot_repository,
            )

            reconciliation_service = AccountReconciliationService(
                account_repository
            )
            reconciliation = reconciliation_service.reconcile()

            # Report accounts that require attention.
            if reconciliation.pending_registration:
                print("\nPending Registration:")
                for config in reconciliation.pending_registration:
                    print(
                        f"  - {getattr(config, 'name', '<unnamed>')} "
                        f"(Account: {config.account_number})"
                    )

            if reconciliation.historical_accounts:
                print("\nHistorical / Inactive Accounts:")
                for account in reconciliation.historical_accounts:
                    print(
                        f"  - {getattr(account, 'name', '<unnamed>')} "
                        f"(Account: {account.account_number})"
                    )

            if reconciliation.duplicate_accounts:
                print("\nDuplicate / Ambiguous Accounts:")
                for duplicate in reconciliation.duplicate_accounts:
                    print(
                        f"  - {duplicate.normalized_account_number} "
                        f"(Source: {duplicate.source}, "
                        f"Records: {len(duplicate.records)})"
                    )

            # Convert reconciliation matches to the tuple format
            # expected by the existing CLI selection functions.
            matches = [
                (match.database_account, match.account_config)
                for match in reconciliation.active_accounts
            ]

            if args.list_accounts:
                if not matches:
                    print("\nNo active accounts were found.")
                    return 1
                print("\nActive Accounts:")
                display_accounts(matches)
                return 0

            if not matches:
                raise ValueError(
                    "No active accounts are available for drift detection. "
                    "Review the reconciliation report above."
                )

            database_account, account_config = select_account(
                matches,
                args.account,
            )

            result = service.evaluate_account(
                database_account,
                account_config,
            )

            account_name = getattr(
                account_config,
                "name",
                getattr(database_account, "name", "<unnamed>"),
            )
            print(f"\nDrift Detection: {account_name}")

            if result.snapshot is None:
                print(result.message or "No stored snapshot exists.")
                return 0

            print(f"Snapshot ID: {result.snapshot.id}")
            print(f"Snapshot date: {result.snapshot_date or 'Unknown'}")
            print(f"Result rows: {len(result.rows)}")
            print(json.dumps(result.rows, indent=2, default=str))

        return 0

    except AccountReconciliationServiceError as exc:
        logger.exception("Account reconciliation failed.")
        print(
            f"Account reconciliation failed: {exc}",
            file=sys.stderr,
        )
        return 1

    except (ValueError, EOFError, KeyboardInterrupt) as exc:
        if isinstance(exc, KeyboardInterrupt):
            print("\nDrift detection cancelled.")
            return 130
        if isinstance(exc, EOFError):
            print("\nNo interactive input available. Supply --account.")
            return 1
        logger.warning("Drift detection could not complete: %s", exc)
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    except Exception:
        logger.exception("Unexpected error in drift detection CLI.")
        print(
            "Drift detection failed. Check the application logs.",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())

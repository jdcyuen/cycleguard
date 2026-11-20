from services.account_reconciliation_orchestration_service import (
    AccountReconciliationOrchestrationService,
)
from models.account_reconciliation_result import (
    AccountReconciliationResult,
)
from models.import_result import ImportResult
from repositories.account_repo import AccountRepository

from datetime import date
from datetime import datetime
from pathlib import Path
from typing import Optional
import re
from core.logger import get_logger

logger = get_logger(__name__)

def extract_snapshot_date(
    filename: str,
) -> Optional[date]:
    """
    Extracts a snapshot date from a positions
    filename.

    Expected format:

        Portfolio_Positions_Mon_DD_YYYY.csv

    Example:

        Portfolio_Positions_Jan_10_2026.csv

    Returns:
        date if found, otherwise None.
    """

    basename = Path(filename).name

    match = re.search(
        r"^Portfolio_Positions_([A-Za-z]{3,9})[-_](\d{1,2})[-_](\d{4})\.csv$",
        basename,
        re.IGNORECASE,
    )

    if not match:

        logger.debug(
            "No snapshot date found in filename '%s'.",
            basename,
        )

        return None

    month_str, day, year = match.groups()

    #
    # Try abbreviated month (Jan)
    #
    try:

        parsed_date = datetime.strptime(
            f"{month_str} {day} {year}",
            "%b %d %Y",
        ).date()

        logger.debug(
            "Extracted snapshot date %s from '%s'.",
            parsed_date,
            basename,
        )

        return parsed_date

    #
    # Try full month (January)
    #
    except ValueError:

        try:

            parsed_date = datetime.strptime(
                f"{month_str} {day} {year}",
                "%B %d %Y",
            ).date()

            logger.debug(
                "Extracted snapshot date %s from '%s'.",
                parsed_date,
                basename,
            )

            return parsed_date

        except ValueError:

            logger.warning(
                "Invalid snapshot date in filename '%s'.",
                basename,
            )

            return None

def resolve_snapshot_date(
    filename: str,
    cli_snapshot_date: Optional[date],
) -> date:
    """
    Resolves the snapshot date for an import.

    Resolution rules:

        1. If --snapshot-date is not supplied:
           • Use the date parsed from the filename.
           • If no date can be parsed, use today's date.

        2. If --snapshot-date is supplied:
           • If the filename contains no date,


             use the CLI date.
           • If the filename date matches the CLI date,
             use the CLI date.
           • If they differ, prompt the user to
             choose which date to use.
    """

    filename_date = extract_snapshot_date(filename)
    logger.info(
                "Snapshot date derived "
                "from filename: %s",
                filename_date,
            )


    #
    # No CLI date supplied
    #
    if cli_snapshot_date is None:

        if filename_date is not None:

            logger.info(
                "Using snapshot date derived "
                "from filename: %s",
                filename_date,
            )

            return filename_date

        today = date.today()

        logger.warning(
            "Unable to derive snapshot date "
            "from filename. "
            "Using today's date: %s",
            today,
        )

        return today

    #
    # CLI date supplied
    #
    if filename_date is None:

        logger.info(
            "Filename contains no snapshot date. "
            "Using CLI snapshot date: %s",
            cli_snapshot_date,
        )

        return cli_snapshot_date

    #
    # Dates agree
    #
    if filename_date == cli_snapshot_date:

        logger.info(
            "CLI snapshot date matches "
            "filename date: %s",
            cli_snapshot_date,
        )

        return cli_snapshot_date

    #
    # Conflict
    #
    print()
    print("WARNING")
    print()
    print(
        "The snapshot date derived from the "
        "filename does not match the "
        "snapshot date supplied on the "
        "command line."
    )
    print()
    print(f"Filename               : {filename}")
    print(
        f"Filename snapshot date : "
        f"{filename_date}"
    )
    print(
        f"CLI snapshot date      : "
        f"{cli_snapshot_date}"
    )
    print()

    while True:

        choice = input(
            "Use the CLI snapshot date? "
            "[Y/N]: "
        ).strip().lower()

        if choice in ("", "y", "yes"):

            logger.warning(
                "User selected CLI snapshot "
                "date: %s",
                cli_snapshot_date,
            )

            return cli_snapshot_date

        if choice in ("n", "no"):

            logger.warning(
                "User selected filename "
                "snapshot date: %s",
                filename_date,
            )

            return filename_date

        print("Please enter 'y' or 'n'.")


def confirm_import(import_type: str, account_name: str,) -> bool:

    answer = input(
        f"\nImport {import_type} "
        f"for '{account_name}'? (y/n): "
    )

    return answer.lower() == "y"


def display_results(result: ImportResult) -> None:
    """
    Display a summary of the completed import.
    """

    print()
    print("=" * 60)
    print(f"{result.import_type.title()} Import Summary")
    print("=" * 60)
    print()

    print("Account")
    print("-------")
    print(f"Account           : {result.account_name}")


    print()

    print("Source")
    print("------")
    print(f"Filename          : {result.filename}")
    print(f"Snapshot Date     : {result.snapshot_date}")
    print()

    print("Results")
    print("-------")
    print(f"Rows Read         : {result.rows_read}")
    print(f"Rows Imported     : {result.rows_imported}")
    print(f"Rows Skipped      : {result.rows_skipped}")

    print()

    print("Database")
    print("--------")
    print(f"Import History ID : {result.import_history_id}")

    if result.snapshot_id is not None:
        print(f"Snapshot ID       : {result.snapshot_id}")

    print()

    print("Performance")
    print("-----------")
    print(f"Elapsed Time      : {result.elapsed_ms:,} ms")
    print(f"Status            : {result.status}")

    if result.warnings:
        print()
        print("Warnings")
        print("--------")
        for warning in result.warnings:
            print(f"- {warning}")

    print()

def confirm_add_account(
    account_name: str,
) -> bool:
    """
    Prompt the user to add a new account.
    """

    logger.info(
        f"Prompting to add account "
        f"'{account_name}'."
    )

    answer = input(
        f"\nAccount '{account_name}' is not in the "
        f"accounts table.\n"
        f"Add it from its YAML configuration? (y/n): "
    ).strip().lower()

    confirmed = answer == "y"

    logger.info(
        "User %s adding account '%s'.",
        "confirmed" if confirmed else "declined",
        account_name,
    )

    return confirmed


def resolve_account(
    account_name: str | None,
    account_repo: AccountRepository,
) -> str:
    """
    Resolve an account using shared reconciliation
    and registration services.

        Case 1:
            --account supplied

            • Check whether the account is active
              through reconciliation.

            • If pending registration, ask for
              confirmation before registering it
              from its YAML configuration.

            • Reconcile again and verify successful
              registration before proceeding.

        Case 2:
            --account omitted

            • Display active reconciled accounts.

            • Prompt the user to select an account.
    """

    orchestration_service: AccountReconciliationOrchestrationService = (
		AccountReconciliationOrchestrationService(account_repo)
	)

    reconciliation: AccountReconciliationResult = (
        orchestration_service.reconcile()
    )

    #
    # Case 1: Explicit account name supplied
    #
    if account_name:

        # Check reconciled active accounts.
        for match in reconciliation.active_accounts:

            if (
                match.database_account.name.lower()
                == account_name.lower()
            ):
                return match.database_account.name

        # Check pending registration accounts.
        pending_config = next(
            (
                config
                for config in reconciliation.pending_registration
                if config.display_name.lower()
                == account_name.lower()
            ),
            None,
        )

        if pending_config is None:
            raise ValueError(
                f"Account '{account_name}' is not an active "
                "account or a pending YAML-configured account."
            )

        logger.info(
            "Account '%s' is pending registration.",
            account_name,
        )

        registered_account = (
            orchestration_service.register_pending_account(
                pending_config.account_number,
                lambda config: confirm_add_account(
                    config.display_name
                ),
            )
        )

        if registered_account is None:
            raise SystemExit("Import cancelled.")

        logger.info(
            "Account '%s' successfully registered "
            "and reconciled.",
            registered_account.name,
        )

        return registered_account.name

    #
    # Case 2: Account name omitted
    #
    accounts = [
        match.database_account
        for match in reconciliation.active_accounts
    ]

    if not accounts:
        raise ValueError(
            "No active reconciled accounts are available."
        )

    print("\nAvailable Accounts:\n")

    for i, account in enumerate(accounts, start=1):
        print(f"{i}. {account.name}")

    while True:

        choice = input("\nSelect account: ")

        try:
            index = int(choice) - 1

        except ValueError:
            print("Please enter a valid number.")
            continue

        if index < 0 or index >= len(accounts):
            print(
                "Selection out of range. "
                "Please choose one of the listed accounts."
            )
            continue

        return accounts[index].name

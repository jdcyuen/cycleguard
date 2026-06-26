from ingestion.common.account_resolver import (
    AccountResolver,
)


def resolve_account(account_name: str | None) -> str:

    #Resolve account from command line or prompt.
    acct_resolver = AccountResolver()

    return acct_resolver.resolve_account(account_name)

import re
from datetime import datetime, date


def resolve_snapshot_date(snapshot_date: str, csv_file: str) -> str:
    """
    Priority:
    1. CLI argument
    2. Filename parsing
    3. Today
    """
    
    # ------------------------
    # 1. CLI argument
    # ------------------------
    if snapshot_date:
        return snapshot_date

    # ------------------------
    # 2. Filename parsing
    # ------------------------
    filename = csv_file.split("/")[-1]

    # Expected: Portfolio_Positions_Jan_10_2026.csv
    match = re.search(
        r"Portfolio_Positions_([A-Za-z]{3,9})_(\d{1,2})_(\d{4})",
        filename
    )

    if match:
        month_str, day, year = match.groups()

        try:
            parsed_date = datetime.strptime(
                f"{month_str} {day} {year}",
                "%b %d %Y"
            )
            return parsed_date.date().isoformat()
        except ValueError:
            # fallback if month abbreviation fails (Jan vs January)
            try:
                parsed_date = datetime.strptime(
                    f"{month_str} {day} {year}",
                    "%B %d %Y"
                )
                return parsed_date.date().isoformat()
            except ValueError:
                pass

    # ------------------------
    # 3. fallback: today
    # ------------------------
    return date.today().isoformat()


def confirm_import(import_type: str, account_name: str,) -> bool:
    
    #Prompt user before import.
    answer = input(
        f"\nImport {import_type} "
        f"for '{account_name}'? (y/n): "
    )

    return answer.lower() == "y"


def display_results(account_name: str, result,) -> None:

    #Display import summary.
    print("\nImport Complete")
    print(f"Account      : {account_name}")
    print(f"Rows Imported: {result.rows_imported}")
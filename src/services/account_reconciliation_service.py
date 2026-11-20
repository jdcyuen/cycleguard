
"""
Account Reconciliation Service
=============================

Purpose
-------
Reconciles account configurations maintained in YAML with account
records stored in the CycleGuard PostgreSQL database.

The service establishes a consistent view of account identity and
lifecycle across CycleGuard applications, ensuring that accounts
are correctly matched before being used in portfolio analysis,
drift detection, or deployment workflows.

How It Works
------------
1. Configuration Loading
   Loads all account configurations through AccountConfigLoader
   from the configured account YAML directory.

2. Database Retrieval
   Retrieves existing account records through AccountRepository.

3. Account Number Normalization
   Normalizes account numbers before comparison by:
       - Removing all whitespace.
       - Converting alphabetic characters to uppercase.
       - Preserving punctuation, including hyphens.

   Account names and display names are not used as identity keys.

4. Account Grouping
   Groups YAML configurations and database records independently
   by their normalized account numbers.

5. Duplicate Detection
   Identifies normalized account numbers appearing more than
   once among YAML configurations.

   PostgreSQL independently enforces normalized account-number
   uniqueness for database records.

   Duplicate YAML identities are considered ambiguous and
   excluded from normal lifecycle classifications.

6. Account Classification
   Compares the unique normalized account numbers across both
   sources and classifies accounts into four categories:

       ACTIVE
           Exactly one YAML configuration and one database
           record share the same normalized account number.

       PENDING REGISTRATION
           A YAML configuration exists without a matching
           database account record.

       HISTORICAL / INACTIVE
           A database account record exists without a matching
           YAML configuration.

       DUPLICATE / AMBIGUOUS
           A YAML account number occurs more than once and
           cannot be safely classified.

7. Reconciliation Results
   Returns an AccountReconciliationResult containing the
   classified accounts and duplicate information for use
   by calling applications.

Algorithms
---------
Account Identity Normalization
    N(account_number) = uppercase(account_number with all
    whitespace removed)

    Punctuation is preserved. Blank or missing account
    numbers are invalid.

Set-Based Reconciliation
    Let Y be the set of unique normalized account numbers
    from YAML configurations.

    Let D be the set of unique normalized account numbers
    from database records.

    Active accounts:
        Y ∩ D

    Pending registration:
        Y - D

    Historical / inactive:
        D - Y

Duplicate Detection
    YAML configurations are grouped by normalized account
    number before classification.

    Any YAML account number with a group size greater
    than one is marked ambiguous and excluded from
    normal classification.

    PostgreSQL independently enforces normalized
    account-number uniqueness for database records.

    This prevents ambiguous YAML configurations from
    being incorrectly activated or registered.

CycleGuard Architecture
----------------------
Account Reconciliation Service is a domain service within
the CycleGuard service layer.

    AccountConfigLoader
           |
           v
    YAML Account Configurations
           |
           +-------------------------+
                                     |
                                     v
                         Account Reconciliation
                                Service
                                     ^
                                     |
           +-------------------------+
           |
    AccountRepository
           |
           v
    PostgreSQL Accounts Table


The service depends on AccountConfigLoader and
AccountRepository for data retrieval. It does not directly
implement YAML parsing, SQL queries, or database connection
management.

Integration Points
-----------------
The reconciliation service provides a shared account lifecycle
and identity mechanism for:

    CLI
        Reports account status and requires explicit
        authorization for registration.

    Standalone Drift Detection Dashboard
        Determines which accounts are eligible for
        drift detection.

    Main CycleGuard Dashboard
        Validates account identity before account-specific
        portfolio aggregation and deployment workflows.

    Other Account-Based Services
        Can consume reconciliation results without
        duplicating account matching logic.

Responsibilities and Boundaries
---------------------------
The service is responsible for:
    - Matching account configurations to database records.
    - Determining account lifecycle status.
    - Detecting ambiguous account identities.
    - Providing structured reconciliation results.

The service does not:
    - Create or modify YAML configurations.
    - Automatically register pending accounts.
    - Delete historical database accounts.
    - Import financial institution files.
    - Create portfolio snapshots or modify positions.
    - Calculate portfolio drift or deployment recommendations.
    - Execute trades.

Data Integrity
-------------
Reconciliation is read-only.

A successful reconciliation requires both configuration
loading and database retrieval to complete successfully.

Invalid or incomplete source data must not result in
a partial or misleading reconciliation report.

Historical database records and their associated portfolio
history are preserved.

Duplicate account identities must be resolved before
normal account workflows can safely proceed.
"""


from dataclasses import dataclass
from typing import TypeVar

from core.logger import get_logger
from config.account_config_loader import AccountConfigLoader
from models.account_match import AccountMatch
from models.account_duplicate import AccountDuplicate
from models.account_reconciliation_result import (
    AccountReconciliationResult,
)
from models.account import Account
from models.account_config import AccountConfig
from repositories.account_repo import AccountRepository


logger = get_logger(__name__)

_AccountRecord = TypeVar(
    "_AccountRecord",
    Account,
    AccountConfig,
)


class AccountReconciliationServiceError(Exception):
    """Raised when account reconciliation cannot complete."""


def normalize_account_number(value: str | None) -> str:
    """
    Normalize account numbers for consistent matching.

    Removes all whitespace and converts letters to uppercase.
    Preserves punctuation, including hyphens.
    """
    if value is None:
        return ""

    return "".join(str(value).split()).upper()


class AccountReconciliationService:
    """
    Reconciles YAML account configurations with database accounts.

    This service is read-only. It does not register or delete accounts.
    """

    def __init__(
        self,
        account_repo: AccountRepository,
        loader: AccountConfigLoader | None = None,
    ) -> None:
        self._account_repo = account_repo
        self._loader = (
            loader
            if loader is not None
            else AccountConfigLoader()
        )

        logger.info(
            "Account reconciliation service initialized."
        )

    def reconcile(self) -> AccountReconciliationResult:
        """
        Classify configured and database accounts.

        Duplicate account numbers are excluded from normal classifications.
        Invalid or incomplete source data prevents reconciliation.
        """
        logger.info("Starting account reconciliation.")

        try:
            configurations = self._loader.load()
        except Exception as exc:
            logger.exception("Failed to load account configurations.")
            raise AccountReconciliationServiceError(
                "Account configuration loading failed."
            ) from exc

        try:
            database_accounts = self._account_repo.list_accounts()
        except Exception as exc:
            logger.exception("Failed to load database accounts.")
            raise AccountReconciliationServiceError(
                "Database account retrieval failed."
            ) from exc

        logger.info(
            "Loaded %d YAML configurations and %d database accounts.",
            len(configurations),
            len(database_accounts),
        )

        configs_by_number = self._group_by_account_number(
            configurations,
            source="YAML",
        )
        database_by_number = self._group_by_account_number(
            database_accounts,
            source="database",
        )

        result = AccountReconciliationResult()

        # Detect duplicate account numbers in YAML configurations.
        # PostgreSQL independently enforces database account-number uniqueness.
        ambiguous_numbers: set[str] = set()

        for number, records in configs_by_number.items():
            if len(records) > 1:
                ambiguous_numbers.add(number)

                result.duplicate_accounts.append(
                    AccountDuplicate(
                        normalized_account_number=number,
                        records=records,
                    )
                )

        all_numbers = set(configs_by_number) | set(database_by_number)

        for number in all_numbers:
            if number in ambiguous_numbers:
                continue

            configs = configs_by_number.get(number, [])
            database_records = database_by_number.get(number, [])

            if configs and database_records:
                result.active_accounts.append(
                    AccountMatch(
                        database_account=database_records[0],
                        account_config=configs[0],
                    )
                )
            elif configs:
                result.pending_registration.append(configs[0])
            elif database_records:
                result.historical_accounts.append(database_records[0])

        logger.info(
            "Account reconciliation completed: "
            "%d active, %d pending, %d historical, %d duplicate groups.",
            len(result.active_accounts),
            len(result.pending_registration),
            len(result.historical_accounts),
            len(result.duplicate_accounts),
        )

        if result.duplicate_accounts:
            logger.warning(
                "Duplicate account numbers detected. "
                "Ambiguous accounts were excluded from normal classifications."
            )

        return result

    @staticmethod
    def _group_by_account_number(
        records: list[_AccountRecord],
        source: str,
    ) -> dict[str, list[_AccountRecord]]:
        """Group records by normalized account number."""
        grouped: dict[str, list[_AccountRecord]] = {}

        for record in records:
            number = normalize_account_number(record.account_number)

            if not number:
                logger.error(
                    "A %s account has a missing or blank account number.",
                    source,
                )
                raise AccountReconciliationServiceError(
                    f"A {source} account has a missing account number."
                )

            grouped.setdefault(number, []).append(record)

        return grouped

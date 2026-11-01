
"""
Account Reconciliation Service
===============================

Module
------
src/services/account_reconciliation_service.py

Purpose
-------
Reconciles account configurations stored in YAML files with account
records stored in the CycleGuard PostgreSQL database.

The service establishes a consistent account lifecycle by determining
which accounts are active, awaiting registration, historical, or
ambiguous because of duplicate account numbers.

Account Identity
----------------
Account identity is determined by normalized account number, not by
account name or display name.

Normalization rules:
    - Remove all whitespace.
    - Convert alphabetic characters to uppercase.
    - Preserve punctuation, including hyphens.
    - Treat None or blank values as invalid account identifiers.

Account Lifecycle
-----------------
1. ACTIVE
   A valid YAML configuration and exactly one database record share
   the same normalized account number.

   Active accounts are eligible for normal CycleGuard account workflows.

2. PENDING REGISTRATION
   A valid YAML configuration exists, but no matching database record
   exists.

   Registration requires explicit authorization through the calling
   application. Accounts must never be registered automatically.

3. HISTORICAL / INACTIVE
   A database record exists, but no matching YAML configuration exists.

   Historical records and their associated portfolio history must be
   preserved. The service must never automatically delete database
   accounts.

4. DUPLICATE / AMBIGUOUS
   A normalized account number appears more than once in either the
   YAML configurations or database records.

   Ambiguous accounts are excluded from normal lifecycle classifications.
   They must be resolved before activation or registration.

Responsibilities
----------------
- Load all valid YAML account configurations.
- Retrieve existing database account records.
- Normalize account numbers consistently.
- Match YAML configurations to database records.
- Identify active, pending, historical, and duplicate accounts.
- Return a structured reconciliation report.
- Log reconciliation activity and operational errors.

Non-Responsibilities
--------------------
This service does not:
    - Create or modify YAML account configurations.
    - Automatically register pending accounts.
    - Delete historical database accounts.
    - Delete or modify portfolio snapshots, positions, or transactions.
    - Import financial institution files.
    - Execute trades or modify portfolio allocations.
    - Perform drift calculations.

Registration Authorization
--------------------------
Account registration is a separate, explicitly authorized operation.

Calling applications are responsible for obtaining user authorization:
    - Streamlit applications require an explicit confirmation action.
    - CLI registration requires an explicit authorization argument.

Registration must recheck database account numbers immediately before
insertion. Database-level uniqueness protection is also required to
protect against concurrent registration attempts.

Architecture and SOLID Principles
---------------------------------
The service follows these design principles:

Single Responsibility:
    Handles account reconciliation and lifecycle classification.

Open/Closed:
    Uses structured result objects that can be extended without
    changing repository behavior.

Liskov Substitution:
    Depends on the behavior of injected loader and repository
    dependencies rather than requiring specific concrete implementations.

Interface Segregation:
    Uses existing loader and repository methods without expanding
    their interfaces unnecessarily.

Dependency Inversion:
    Receives the account repository and configuration loader through
    constructor injection.

Dependencies
------------
- AccountConfigLoader
- AccountRepository
- Account model
- Python dataclasses
- Project logging utility

Exceptions
----------
AccountReconciliationServiceError:
    Raised when configuration loading, database retrieval, or
    reconciliation cannot complete reliably.

Source-level exceptions are preserved as the original exception cause.

Logging
-------
Uses the CycleGuard logging framework.

Logs include:
    - Reconciliation start and completion.
    - Number of YAML and database records examined.
    - Account lifecycle classification counts.
    - Duplicate account detection.
    - Configuration and database failures.

Account numbers and other unnecessary sensitive information must not
be included in log messages.

Data Safety
-----------
Reconciliation is read-only.

A failed or incomplete configuration/database read must not produce
a misleading reconciliation report.

Historical database records are preserved.

Duplicate or ambiguous account identities must not be activated or
registered automatically.

Usage
-----
    service = AccountReconciliationService(
        account_repo=account_repository,
        loader=AccountConfigLoader(),
    )

    result = service.reconcile()

    active_accounts = result.active_accounts
    pending_accounts = result.pending_registration
    historical_accounts = result.historical_accounts
    duplicate_accounts = result.duplicate_accounts

Testing
-------
Unit tests are maintained in:

    tests/services/test_account_reconciliation_service.py

Tests should cover:
    - Account-number normalization.
    - All lifecycle classifications.
    - Duplicate detection in YAML and database records.
    - Missing or invalid account numbers.
    - Configuration and database retrieval failures.
    - Logging and exception propagation.
    - Registration authorization and duplicate protection.

Status
------
Initial implementation: Read-only reconciliation.

Registration and application integrations are implemented separately
after reconciliation behavior and database uniqueness safeguards
have been verified.
"""

from dataclasses import dataclass, field
from typing import Any

from core.logger import get_logger
from config.account_config_loader import AccountConfigLoader

logger = get_logger(__name__)


class AccountReconciliationServiceError(Exception):
    """Raised when account reconciliation cannot complete."""


@dataclass(slots=True)
class AccountMatch:
    """A YAML configuration matched to a database account."""

    database_account: Any
    account_config: Any


@dataclass(slots=True)
class AccountDuplicate:
    """An account number appearing more than once in a source."""

    normalized_account_number: str
    source: str
    records: list[Any] = field(default_factory=list)


@dataclass(slots=True)
class AccountReconciliationResult:
    """Complete account reconciliation report."""

    active_accounts: list[AccountMatch] = field(default_factory=list)
    pending_registration: list[Any] = field(default_factory=list)
    historical_accounts: list[Any] = field(default_factory=list)
    duplicate_accounts: list[AccountDuplicate] = field(default_factory=list)

    @property
    def has_duplicates(self) -> bool:
        return bool(self.duplicate_accounts)


def normalize_account_number(value: Any) -> str:
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

    def __init__(self, account_repo, loader=None):
        self._account_repo = account_repo
        self._loader = loader if loader is not None else AccountConfigLoader()

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

        duplicate_numbers = set()

        for source_groups, source_name in (
            (configs_by_number, "YAML"),
            (database_by_number, "database"),
        ):
            for number, records in source_groups.items():
                if len(records) > 1:
                    duplicate_numbers.add((source_name, number))
                    result.duplicate_accounts.append(
                        AccountDuplicate(
                            normalized_account_number=number,
                            source=source_name,
                            records=records,
                        )
                    )

        ambiguous_numbers = {
            number for _, number in duplicate_numbers
        }

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
    def _group_by_account_number(records, source: str) -> dict[str, list[Any]]:
        """Group records by normalized account number."""
        grouped: dict[str, list[Any]] = {}

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

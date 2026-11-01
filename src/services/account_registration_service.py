
"""
Account Registration Service
=============================

Purpose
-------
Safely register a valid YAML-configured account in the CycleGuard
database when no matching database account exists.

ACCOUNT REGISTRATION RULES
--------------------------
1. Only accounts identified as pending registration by
   AccountReconciliationService may be offered for registration.

2. Registration requires a valid account configuration containing:
   - A nonblank account number.
   - A nonblank display name.
   - A nonblank financial institution.

3. Account numbers are normalized before comparison:
   - All whitespace is removed.
   - Letters are converted to uppercase.
   - Punctuation is preserved.

4. The normalized account number must be unique across the database.

5. The service checks for an existing account immediately before
   attempting insertion.

6. The database normalized unique index is the final safeguard
   against concurrent registrations.

7. Registration must be explicitly authorized by the user.
   Discovering a YAML configuration never triggers automatic insertion.

8. A successful registration creates a database account using:
   - account_number: normalized YAML account number
   - name: YAML display_name
   - institution: YAML institution

9. Existing accounts and historical records are never deleted or
   modified by this service.

10. Account reconciliation must run again after successful registration
    so the new account can be classified as active.

DESIGN PRINCIPLES
-----------------
- Single Responsibility: this service handles registration only.
- Open/Closed: repository implementations can change without changing
  registration business rules.
- Liskov Substitution: any repository satisfying the protocol can be used.
- Interface Segregation: only two repository operations are required.
- Dependency Inversion: the service depends on a repository protocol,
  not a concrete database implementation.

EXCEPTION POLICY
----------------
- Validation errors identify invalid configuration.
- Conflict errors identify duplicate account numbers.
- Registration errors identify other registration failures.
- Original exceptions are preserved through exception chaining.
"""

from typing import Protocol, Optional

import psycopg2

from core.logger import get_logger
from models.account import Account
from services.account_reconciliation_service import (
    normalize_account_number,
)


logger = get_logger(__name__)


class AccountRepositoryProtocol(Protocol):
    """Minimal repository contract required for account registration."""

    def get_by_account_number(
        self,
        account_number: str,
    ) -> Optional[Account]:
        ...

    def create(
        self,
        account: Account,
    ) -> Account:
        ...


class AccountRegistrationError(Exception):
    """Base exception for account registration failures."""


class AccountRegistrationValidationError(AccountRegistrationError):
    """Raised when registration configuration is invalid."""


class AccountRegistrationConflictError(AccountRegistrationError):
    """Raised when the account number is already registered."""


class AccountRegistrationService:
    """Validate and register pending account configurations."""

    def __init__(
        self,
        account_repository: AccountRepositoryProtocol,
    ) -> None:

        if account_repository is None:
            raise ValueError(
                "An account repository is required."
            )

        self.account_repository = account_repository

        logger.debug(
            "AccountRegistrationService initialized."
        )

    def register(
        self,
        account_config,
    ) -> Account:
        """
        Register an account after explicit authorization by the caller.

        The caller is responsible for ensuring that the configuration
        belongs to the reconciliation service's pending-registration list.
        """

        logger.info(
            "Account registration requested."
        )

        account_number, display_name, institution = (
            self._validate_configuration(account_config)
        )

        logger.info(
            "Validating registration for account '%s' at '%s'.",
            display_name,
            institution,
        )

        self._check_for_existing_account(account_number)

        account = Account(
            account_number=account_number,
            name=display_name,
            institution=institution,
        )

        try:
            created_account = self.account_repository.create(
                account
            )

            if created_account is None:
                raise AccountRegistrationError(
                    "Repository returned no account after insertion."
                )

            logger.info(
                "Successfully registered account '%s' (database ID: %s).",
                created_account.name,
                created_account.id,
            )

            return created_account

        except AccountRegistrationError:
            raise

        except Exception as exc:
            if self._is_unique_constraint_violation(exc):
                logger.warning(
                    "Concurrent registration conflict for account '%s'.",
                    display_name,
                )

                raise AccountRegistrationConflictError(
                    "An account with this account number was registered "
                    "by another operation."
                ) from exc

            logger.exception(
                "Unexpected database or repository failure registering "
                "account '%s'.",
                display_name,
            )

            raise AccountRegistrationError(
                f"Unable to register account '{display_name}'."
            ) from exc

    def _validate_configuration(
        self,
        account_config,
    ) -> tuple[str, str, str]:
        """Validate and normalize registration configuration."""

        if account_config is None:
            logger.warning(
                "Registration rejected: account configuration is missing."
            )

            raise AccountRegistrationValidationError(
                "Account configuration is required."
            )

        account_number = normalize_account_number(
            getattr(account_config, "account_number", None)
        )

        display_name = (
            getattr(account_config, "display_name", None) or ""
        ).strip()

        institution = (
            getattr(account_config, "institution", None) or ""
        ).strip()

        missing_fields = []

        if not account_number:
            missing_fields.append("account number")

        if not display_name:
            missing_fields.append("display name")

        if not institution:
            missing_fields.append("institution")

        if missing_fields:
            logger.warning(
                "Registration rejected for invalid configuration. "
                "Missing fields: %s.",
                ", ".join(missing_fields),
            )

            raise AccountRegistrationValidationError(
                "Missing required registration fields: "
                + ", ".join(missing_fields)
                + "."
            )

        logger.debug(
            "Registration configuration validated for '%s'.",
            display_name,
        )

        return account_number, display_name, institution

    def _check_for_existing_account(
        self,
        account_number: str,
    ) -> None:
        """Reject an account number that already exists."""

        try:
            existing_account = (
                self.account_repository.get_by_account_number(
                    account_number
                )
            )

        except Exception as exc:
            logger.exception(
                "Unable to verify account uniqueness before registration."
            )

            raise AccountRegistrationError(
                "Unable to verify whether the account is already registered."
            ) from exc

        if existing_account is not None:
            logger.warning(
                "Registration rejected: account number already exists "
                "(database ID: %s).",
                existing_account.id,
            )

            raise AccountRegistrationConflictError(
                "An account with this account number is already registered."
            )

        logger.debug(
            "Account uniqueness check passed."
        )
  
    @staticmethod
    def _is_unique_constraint_violation(
        exception: Exception,
    ) -> bool:
        """Inspect chained exceptions for a PostgreSQL unique violation."""

        current_exception = exception
        visited = set()

        while current_exception is not None:
            if id(current_exception) in visited:
                break

            visited.add(id(current_exception))

            if isinstance(
                current_exception,
                psycopg2.errors.UniqueViolation,
            ):
                return True

            if (
                isinstance(current_exception, psycopg2.IntegrityError)
                and getattr(
                    getattr(current_exception, "diag", None),
                    "sqlstate",
                    None,
                ) == "23505"
            ):
                return True

            current_exception = (
                current_exception.__cause__
                or current_exception.__context__
            )

        return False


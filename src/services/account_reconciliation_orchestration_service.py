
"""
Account Reconciliation Orchestration Service
============================================

Purpose
-------
Coordinates account reconciliation and account registration across
CycleGuard application interfaces.

Why It Is Needed
----------------
AccountReconciliationService identifies the lifecycle status of
configured accounts, while AccountRegistrationService safely creates
a database account record.

Neither service should be responsible for application-specific
approval workflows.

Without a shared orchestration layer, CLI, Streamlit, and UI workflows
could implement their own registration rules, resulting in inconsistent
account matching, missing approval checks, or unsafe database changes.

This service provides one shared business workflow for all interfaces.

How It Works
------------
1. Reconciliation
   Calls AccountReconciliationService to load YAML configurations,
   retrieve database accounts, and classify account lifecycle status.

2. Ambiguity Protection
   Rejects registration when duplicate account identities are detected.

3. Registration Eligibility
   Matches the requested account number against the pending-registration
   configurations returned by reconciliation.

   Account identity is determined exclusively by normalized account
   number, not by account name or display name.

4. Explicit Approval
   Calls a confirmation callback supplied by the application interface.

   Registration proceeds only when the callback explicitly approves.

5. Registration
   Calls AccountRegistrationService to validate and register the
   pending YAML configuration.

6. Post-Registration Verification
   Runs reconciliation again and confirms that the account is classified
   as active.

Responsibilities and Boundaries
--------------------------------
This service:
    - Coordinates reconciliation and registration.
    - Enforces pending-registration eligibility.
    - Requires explicit approval.
    - Verifies successful registration.

This service does not:
    - Create or modify YAML files.
    - Delete historical accounts.
    - Create positions, snapshots, or transactions.
    - Import CSV files.
    - Implement CLI, Streamlit, or UI presentation logic.
    - Perform account matching independently of reconciliation.
"""

from typing import Any, Callable, Optional

from core.logger import get_logger

from services.account_reconciliation_service import (
    AccountReconciliationService,
    AccountReconciliationServiceError,
    normalize_account_number,
)

from services.account_registration_service import (
    AccountRegistrationService,
    AccountRegistrationError,
)


logger = get_logger(__name__)


class AccountReconciliationOrchestrationError(Exception):
    """Base exception for account orchestration failures."""


class AccountReconciliationAmbiguityError(
    AccountReconciliationOrchestrationError
):
    """Raised when duplicate account identities prevent safe processing."""


class AccountRegistrationEligibilityError(
    AccountReconciliationOrchestrationError
):
    """Raised when an account is not eligible for registration."""


class AccountRegistrationApprovalError(
    AccountReconciliationOrchestrationError
):
    """Raised when the approval callback fails."""


class AccountRegistrationVerificationError(
    AccountReconciliationOrchestrationError
):
    """Raised when registration cannot be verified after creation."""


class AccountReconciliationOrchestrationService:
    """
    Coordinates account reconciliation and approved registration.
    """

    def __init__(
        self,
        account_repo,
        reconciliation_service=None,
        registration_service=None,
    ):
        if account_repo is None:
            raise ValueError("An account repository is required.")

        self._reconciliation_service = (
            reconciliation_service
            if reconciliation_service is not None
            else AccountReconciliationService(account_repo)
        )

        self._registration_service = (
            registration_service
            if registration_service is not None
            else AccountRegistrationService(account_repo)
        )

        logger.info(
            "Account reconciliation orchestration service initialized."
        )

    def reconcile(self):
        """
        Return the current account reconciliation result.

        Raises
        ------
        AccountReconciliationOrchestrationError
            If reconciliation cannot be completed.
        """

        logger.info("Starting account reconciliation orchestration.")

        try:
            result = self._reconciliation_service.reconcile()

            logger.info(
                "Account reconciliation completed: "
                "%d active, %d pending, %d historical, "
                "%d duplicate groups.",
                len(result.active_accounts),
                len(result.pending_registration),
                len(result.historical_accounts),
                len(result.duplicate_accounts),
            )

            return result

        except AccountReconciliationServiceError:
            logger.exception(
                "Account reconciliation failed during orchestration."
            )
            raise

        except Exception as exc:
            logger.exception(
                "Unexpected account reconciliation failure."
            )
            raise AccountReconciliationOrchestrationError(
                "Unable to complete account reconciliation."
            ) from exc

    def register_pending_account(
        self,
        account_number: str,
        confirmation_callback: Callable[[Any], bool],
    ) -> Optional[Any]:
        """
        Register a pending YAML-backed account after explicit approval.

        Parameters
        ----------
        account_number:
            Account number identifying the requested account.

        confirmation_callback:
            Application-provided function receiving the matching
            YAML configuration and returning True or False.

        Returns
        -------
        Account or None
            The newly registered database account when approved.
            None when registration is declined.
        """

        normalized_number = normalize_account_number(account_number)

        if not normalized_number:
            raise AccountRegistrationEligibilityError(
                "A valid account number is required."
            )

        if not callable(confirmation_callback):
            raise AccountRegistrationApprovalError(
                "A valid account confirmation callback is required."
            )

        logger.info(
            "Evaluating registration eligibility for account %s.",
            normalized_number,
        )

        result = self.reconcile()

        if result.has_duplicates:
            logger.error(
                "Registration blocked for account %s: "
                "%d duplicate account groups detected.",
                normalized_number,
                len(result.duplicate_accounts),
            )

            raise AccountReconciliationAmbiguityError(
                "Account registration is blocked because duplicate "
                "account identities must be resolved first."
            )

        matching_pending = [
            config
            for config in result.pending_registration
            if normalize_account_number(config.account_number)
            == normalized_number
        ]

        if len(matching_pending) != 1:
            logger.warning(
                "Account %s is not uniquely pending registration. "
                "Matching pending configurations: %d.",
                normalized_number,
                len(matching_pending),
            )

            raise AccountRegistrationEligibilityError(
                "The requested account does not have exactly one "
                "eligible pending YAML configuration."
            )

        account_config = matching_pending[0]

        logger.info(
            "Account %s is eligible for registration using "
            "configuration '%s'.",
            normalized_number,
            getattr(account_config, "name", "Unknown"),
        )

        try:
            approved = confirmation_callback(account_config)

        except Exception as exc:
            logger.exception(
                "Account registration confirmation failed for %s.",
                normalized_number,
            )

            raise AccountRegistrationApprovalError(
                "Unable to obtain account registration approval."
            ) from exc

        if not isinstance(approved, bool):
            logger.error(
                "Confirmation callback returned an invalid result "
                "for account %s.",
                normalized_number,
            )

            raise AccountRegistrationApprovalError(
                "The confirmation callback must return True or False."
            )

        if not approved:
            logger.info(
                "Account registration declined for %s.",
                normalized_number,
            )
            return None

        logger.info(
            "Registration approved for account %s.",
            normalized_number,
        )

        try:
            registered_account = self._registration_service.register(
                account_config
            )

        except AccountRegistrationError:
            logger.exception(
                "Account registration failed for %s.",
                normalized_number,
            )
            raise

        except Exception as exc:
            logger.exception(
                "Unexpected account registration failure for %s.",
                normalized_number,
            )

            raise AccountReconciliationOrchestrationError(
                "Unexpected failure during account registration."
            ) from exc

        logger.info(
            "Account %s registered successfully. "
            "Verifying registration through reconciliation.",
            normalized_number,
        )

        verification_result = self.reconcile()

        if verification_result.has_duplicates:
            logger.error(
                "Post-registration verification found duplicate "
                "account identities for account %s.",
                normalized_number,
            )

            raise AccountRegistrationVerificationError(
                "The account was registered, but verification detected "
                "duplicate account identities."
            )

        matching_active = [
            match
            for match in verification_result.active_accounts
            if normalize_account_number(
                match.account_config.account_number
            ) == normalized_number
            and normalize_account_number(
                match.database_account.account_number
            ) == normalized_number
        ]

        if len(matching_active) != 1:
            logger.error(
                "Post-registration verification failed for account %s. "
                "Active matches: %d.",
                normalized_number,
                len(matching_active),
            )

            raise AccountRegistrationVerificationError(
                "The account was registered, but reconciliation "
                "could not verify exactly one active account."
            )

        logger.info(
            "Account registration and verification completed "
            "successfully for %s.",
            normalized_number,
        )

        return registered_account

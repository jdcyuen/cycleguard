"""
Account Reconciliation Result
=============================

Contains the complete results of reconciling YAML account
configurations against registered database accounts.

Purpose
-------
Provides a structured report of account status so that
CLI and Streamlit applications can consistently determine
which accounts are active, pending registration, historical,
or duplicated.
"""

from dataclasses import dataclass, field

from models.account import Account
from models.account_config import AccountConfig
from models.account_duplicate import AccountDuplicate
from models.account_match import AccountMatch


@dataclass(slots=True)
class AccountReconciliationResult:
    """
    Complete account reconciliation report.

    Attributes
    ----------
    active_accounts:
        Accounts that have matching YAML configurations
        and database records.

    pending_registration:
        YAML-configured accounts that have not yet been
        registered in the database.

    historical_accounts:
        Database accounts that no longer have a matching
        YAML configuration.

    duplicate_accounts:
        YAML configurations containing duplicate normalized
        account numbers.

    has_duplicates:
        Indicates whether any duplicate account numbers
        were detected.
    """

    # Accounts successfully matched between YAML and database.
    active_accounts: list[AccountMatch] = field(
        default_factory=list
    )

    # YAML accounts awaiting explicit registration.
    pending_registration: list[AccountConfig] = field(
        default_factory=list
    )

    # Database accounts without a matching YAML configuration.
    historical_accounts: list[Account] = field(
        default_factory=list
    )

    # YAML configurations containing duplicate account numbers.
    duplicate_accounts: list[AccountDuplicate] = field(
        default_factory=list
    )

    @property
    def has_duplicates(self) -> bool:
        """Return True when duplicate account configurations exist."""
        return bool(self.duplicate_accounts)
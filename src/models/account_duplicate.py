"""
Account Duplicate
=================

Represents an account number appearing more than once
among YAML account configurations.

Purpose
-------
Allows AccountReconciliationService to identify and report
ambiguous account configurations before registration.

Database account numbers are protected by a PostgreSQL
unique expression index. Therefore, this model specifically
represents YAML configuration duplicates.
"""

from dataclasses import dataclass, field

from models.account_config import AccountConfig


@dataclass(slots=True)
class AccountDuplicate:
    """
    Represents duplicate YAML configurations for one account number.

    Attributes
    ----------
    normalized_account_number:
        The normalized account number shared by the duplicate
        configurations. Normalization makes comparisons
        consistent regardless of letter case or whitespace.

    records:
        The YAML AccountConfig objects containing this
        duplicate account number.

        A list is used because more than two configurations
        could potentially contain the same account number.
        Each entry represents one conflicting configuration.
    """

    # Account number shared by the duplicate configurations.
    normalized_account_number: str

    # All YAML configurations containing this account number.
    # default_factory creates a separate empty list for each instance.
    records: list[AccountConfig] = field(
        default_factory=list
    )
"""
Account Match
=============

Represents a YAML account configuration matched
to a database account.
"""

from dataclasses import dataclass


from models.account import Account
from models.account_config import AccountConfig


@dataclass(slots=True)
class AccountMatch:
    """A YAML configuration matched to a database account."""


	#The account record retrieved from PostgreSQL.
    database_account: Account

	#The corresponding account configuration loaded from YAML.
    account_config: AccountConfig
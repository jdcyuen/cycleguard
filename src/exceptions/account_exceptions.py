# src/exceptions/account_exceptions.py

class NoAccountsFoundError(Exception):
    """No accounts were found in the accounts table."""


class UnknownAccountError(Exception):
    """Requested account does not exist."""


class AccountConfigurationError(Exception):
    """Account YAML configuration is invalid."""
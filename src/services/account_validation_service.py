#src/services/account_validation_service.py

from core.logger import get_logger

from config.account_config_loader import (
    AccountConfigLoader,
)
from models.account import Account

logger = get_logger(__name__)

class AccountValidationServiceError(Exception):
    """Raised when account validation service operations fail."""

class AccountValidationService:
    """
    Validates configured accounts.

    Responsible for:

        • Checking whether an account exists
          in the accounts table.

        • Adding a configured account from
          its YAML configuration.
    """

    def __init__(
        self,
        account_repo,
        loader=None,
    ):

        self._account_repo = account_repo

        self._loader = (
            loader
            if loader is not None
            else AccountConfigLoader()
        )

    def exists(
        self,
        account_name: str,
    ) -> bool:
        """
        Returns True if the account already
        exists in the database.
        """

        logger.info(
            f"Checking if account "
            f"'{account_name}' "
            f"exists in database."
        )

        return (
            self._account_repo.get_by_name(
                account_name
            )
            is not None
        )

    def add_account(
        self,
        account_name: str,
    ):
        """
        Adds a configured account to
        the database.

        Returns:
            Newly created Account.

        Raises:
            ValueError if the account
            configuration does not exist.
        """
        
        config = self._loader.get(account_name)

        if config is None:
            logger.error(f"Account configuration not found: {account_name}")
            raise ValueError(f"Unknown account '{account_name}'.")
        
        account = Account(
            account_number=config.account_number,
            name=config.name,
            institution=config.institution)
        try:
            logger.info( f"Adding account '{account_name}' to database.")
            created_account = self._account_repo.create(account)
            logger.info(f"Account successfully added with name '{account_name}' and id {created_account.id}.")
            return created_account

        except Exception as exc:
            logger.exception(f"Failed to add account '{account_name}'.")
            raise AccountValidationServiceError(f"Failed to add account '{account_name}'.") from exc
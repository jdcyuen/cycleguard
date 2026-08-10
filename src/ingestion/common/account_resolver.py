from core import logger
from typing import List, Optional
from config.config_manager import get_config
from core.logger import get_logger
import json

from services.account_validation_service import (
    AccountValidationService,
)
from ingestion.common.cli_ingestion_helper import confirm_add_account

logger = get_logger(__name__)

class AccountResolver:
    """
    Resolves account names from configuration.

    Used by:
      - cli_ingest_positions.py
      - cli_ingest_transactions.py
      - future Streamlit ingestion UI
    """

    def get_account_names(self) -> List[str]:
        """
        Return configured account names.
        """
        config = get_config()
        accounts = config.get("accounts", {})
        logger.info(f"Configured Accounts: {accounts.keys()}")
        return sorted(accounts.keys())

    def validate_account(self, account_name: str, ) -> bool:
        
        #Returns True if account exists.
        return account_name in self.get_account_names()

    


    def resolve_account(
        self,
        account_name: str | None,
        account_repo,
    ) -> str:
        """
        Resolve the account to use for an import.

        Case 1:
            --account supplied

            • Verify the account exists in the
            accounts table.

            • If not, ask whether it should be
            added from its YAML configuration.

        Case 2:
            --account omitted

            • Display configured accounts from
            the accounts table.

            • Return the selected account.
        """

        validation = AccountValidationService(account_repo )

        #
        # Case 1
        #
        if account_name:

            if validation.exists(account_name):
                return account_name

            print(
                f"\nAccount '{account_name}' does not exist.")

            if not confirm_add_account(account_name ):
                raise SystemExit(
                    "Import cancelled."
                )

            validation.add_account(account_name)

            return account_name

        #
        # Case 2
        #
        accounts = (account_repo.list_accounts())

        if not accounts:
            raise ValueError("No accounts exist in the database." )

        print("\nAvailable Accounts:\n")

        for i, account in enumerate(
            accounts,
            start=1,
        ):

            print(f"{i}. {account.name}" )

        while True:

            choice = input("\nSelect account: ")

            try:

                index = int(choice) - 1

            except ValueError:

                print("Please enter a valid number." )
                continue

            if index < 0 or index >= len(accounts):

                print("Selection out of range. Please choose one of the listed accounts.")
                
                continue

            return accounts[index].name

    

    def prompt_for_account(self) -> str:

        #Prompt the user to choose an account.
        accounts = self.get_account_names()

        if not accounts:
            raise ValueError("No accounts configured.")

        print("\nAvailable Accounts\n")
        for index, account in enumerate(accounts, start=1,):
            print(f"{index}. {account}")

        while True:

            selection = input( "\nSelect account number: ").strip()

            try:
                selection_num = int(selection)
                if 1 <= selection_num <= len(accounts):
                    return accounts[ selection_num - 1 ]

            except ValueError:
                pass

            print("Invalid selection. Please try again.")
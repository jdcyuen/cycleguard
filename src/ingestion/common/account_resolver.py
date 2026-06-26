from typing import List, Optional
from config.config_manager import get_config

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
        return sorted(accounts.keys())

    def validate_account(self, account_name: str, ) -> bool:
        
        #Returns True if account exists.
        return account_name in self.get_account_names()



    def resolve_account(self, account_name: Optional[str] = None,) -> str:
        """
        Resolve an account name.

        If supplied, validate it.

        If omitted, prompt the user to choose one.
        """

        if account_name:

            if not self.validate_account(account_name):

                valid_accounts = ", ".join(self.get_account_names() )

                raise ValueError(
                    f"Unknown account '{account_name}'. "
                    f"Valid accounts: {valid_accounts}"
                )

            return account_name

        return self.prompt_for_account()

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
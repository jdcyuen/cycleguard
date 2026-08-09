from dataclasses import dataclass


@dataclass(slots=True)
class AccountConfig:
    """
    Account configuration loaded from a YAML file.

    Attributes:
        name:
            CycleGuard account identifier
            (e.g. rollover_ira).

        account_number:
            Brokerage account number.

        institution:
            Brokerage provider
            (e.g. Fidelity).

        display_name:
            User-friendly account name.

        risk_profile:
            Account risk profile.
    """

    name: str
    display_name: str
    account_type: str
    risk_profile: str
    account_number: str
    institution: str
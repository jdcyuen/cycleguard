from dataclasses import dataclass


@dataclass(slots=True)
class PositionLimits:
    max_position_pct: float
    overrides: dict[str, float]

@dataclass(slots=True)
class AccountSettings:
    rebalance_frequency: str
    allow_fractional_shares: bool
    enable_recovery_trims: bool
    enable_dynamic_deployment: bool


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
    bucket_mapping: dict[str, str]
    bucket_weights: dict[str, float]
    position_limits: PositionLimits
    settings: AccountSettings
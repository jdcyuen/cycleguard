from pathlib import Path

import yaml

from core.logger import get_logger

from models.account_config import (
    AccountConfig,
    PositionLimits,
    AccountSettings,
)

logger = get_logger(__name__)


class AccountConfigLoader:
    """
    Loads account configuration from
    src/config/accounts.
    """

    def __init__(
        self,
        config_dir: Path | None = None,
    ):

        self._config_dir = (
            Path(config_dir)
            if config_dir
            else (
                Path(__file__).resolve().parent
                / "accounts"
            )
        )

    def load(self) -> list[AccountConfig]:
        """
        Load all configured accounts.
        """

        logger.info(
            f"Loading account configurations "
            f"from '{self._config_dir}'."
        )

        if not self._config_dir.exists():

            raise FileNotFoundError(
                f"Account configuration directory "
                f"not found: {self._config_dir}"
            )

        accounts = []

        for file in sorted(
            self._config_dir.glob("*.yaml")
        ):

            accounts.append(
                self._load_file(file)
            )

        logger.info(
            f"Loaded "
            f"{len(accounts)} account(s)."
        )

        return accounts

    def get(
        self,
        account_name: str,
    ) -> AccountConfig | None:
        """
        Load a single account configuration.

        Returns:
            AccountConfig if found,
            otherwise None.
        """

        file = (
            self._config_dir
            / f"{account_name}.yaml"
        )

        if not file.exists():

            logger.warning(
                f"Account configuration not found: "
                f"{account_name}"
            )

            return None

        return self._load_file(file)

    def _load_file(
        self,
        file: Path,
    ) -> AccountConfig:
        """
        Load one account YAML file.
        """

        logger.debug(
            f"Loading account configuration: "
            f"{file.name}"
        )

        with open(
            file,
            "r",
            encoding="utf-8",
        ) as stream:

            config = yaml.safe_load(stream)

        account = config["account"]

        bucket_mapping = config.get(
            "bucket_mapping",
            {},
        )

        bucket_weights = config.get(
            "bucket_weights",
            {},
        )

        position_limits_data = config.get(
            "position_limits",
            {},
        )

        position_limits = PositionLimits(
            max_position_pct=position_limits_data.get(
                "max_position_pct",
                0.10,
            ),
            overrides=position_limits_data.get(
                "overrides",
                {},
            ),
        )

        settings_data = config.get(
            "settings",
            {},
        )

        settings = AccountSettings(
            rebalance_frequency=settings_data.get(
                "rebalance_frequency",
                "monthly",
            ),
            allow_fractional_shares=settings_data.get(
                "allow_fractional_shares",
                True,
            ),
            enable_recovery_trims=settings_data.get(
                "enable_recovery_trims",
                True,
            ),
            enable_dynamic_deployment=settings_data.get(
                "enable_dynamic_deployment",
                True,
            ),
        )

        return AccountConfig(
            name=account["name"],
            display_name=account["display_name"],
            account_type=account["account_type"],
            risk_profile=account["risk_profile"],
            account_number=account["account_number"],
            institution=account["institution"],
            bucket_mapping=bucket_mapping,
            bucket_weights=bucket_weights,
            position_limits=position_limits,
            settings=settings,
        )
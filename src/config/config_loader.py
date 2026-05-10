from pathlib import Path
from typing import Any, Dict
import yaml

from src.config.schema_validator import (
    ConfigError,
    validate_config,
)


class ConfigLoader:
    """
    Responsible ONLY for:
    - locating the config file
    - loading YAML into a dict
    - delegating validation
    """

    def __init__(self, config_path: str = "config/accounts/rollover_ira.yaml"):
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}

    @classmethod
    def for_account(cls, account_name: str):
        """
        Factory helper for loading a specific account config.
        Example:
            ConfigLoader.for_account("roth_ira")
        """
        path = Path(f"config/accounts/{account_name}.yaml")

        if not path.exists():
            raise FileNotFoundError(f"Unknown account config: {account_name}")

        return cls(path)

    @classmethod
    def available_accounts(cls):
        """
        Dynamically discovers available account configs.
        """
        accounts_dir = Path("config/accounts")

        if not accounts_dir.exists():
            return []

        return sorted([f.stem for f in accounts_dir.glob("*.yaml")])

    # =========================
    # Public API
    # =========================
    def load(self) -> Dict[str, Any]:
        """
        Loads and validates the YAML configuration.
        """
        self._validate_file_exists()

        self.config = self._read_yaml()

        validate_config(self.config)

        return self.config

    # =========================
    # File Handling
    # =========================
    def _validate_file_exists(self) -> None:
        """
        Ensures the config file exists before loading.
        """
        if not self.config_path.exists():
            raise ConfigError(f"Config file not found: {self.config_path}")

    def _read_yaml(self) -> Dict[str, Any]:
        try:
            with open(self.config_path, "r") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigError(f"YAML parsing error: {e}")
        except Exception as e:
            raise ConfigError(f"Unexpected error reading config: {e}")

        if data is None:
            raise ConfigError("Config file is empty")

        if not isinstance(data, dict):
            raise ConfigError("Config root must be a dictionary")

        return data

import os
import yaml
from typing import Any, Dict
from pathlib import Path

from core.logger import get_logger
from config.bucket_target_validator import (
    BucketTargetValidationError,
    validate_bucket_security_targets,
)

from models.account_config import (
    AccountConfig,
    PositionLimits,
    AccountSettings,
)

logger = get_logger(__name__)

class ConfigLoader:
    def __init__(self, config_path: str = None):
        from pathlib import Path
        import os

        # FILE: src/config/config_loader.py
        # This ensures config_path ALWAYS exists

        if config_path is None:
            base_dir = Path(__file__).resolve().parents[2]
            config_path = str(base_dir / "src/config/config.yaml")

        self.config_path = config_path  # 🔥 REQUIRED (this is what is missing)

        self.config_dir = os.path.dirname(__file__)

        self.config = {}

    def load(self) -> Dict[str, Any]:
        # Load base config file
        with open(self.config_path, "r") as f:
            base_config = yaml.safe_load(f) or {}

        self.config = {
            "system": self._load_system_configs(),
            "accounts": self._load_account_configs(),
        }

        # Optional merge with base YAML if needed
        self.config.update(
            {k: v for k, v in base_config.items() if k not in self.config}
        )

        # Backward compatibility layer (for legacy flat access)
        self._inject_legacy_flattened_config()

        return self.config

    # -----------------------------
    # SYSTEM CONFIG LOADER
    # -----------------------------
    def _load_system_configs(self) -> Dict[str, Any]:
        system_dir = os.path.join(self.config_dir, "system")

        # 🔍 DEBUG: add these here
        print("CONFIG DIR:", self.config_dir)
        print("SYSTEM DIR:", system_dir)
        print(
            "FILES:",
            os.listdir(system_dir) if os.path.exists(system_dir) else "NOT FOUND",
        )

        if not os.path.exists(system_dir):
            return {}

        system = {}

        for file in os.listdir(system_dir):
            if file.endswith(".yaml"):
                key = file.replace(".yaml", "")
                system[key] = self._load_yaml(os.path.join(system_dir, file))

        return system

    # -----------------------------
    # ACCOUNT CONFIG LOADER
    # -----------------------------

    def _load_account_configs(self) -> Dict[str, Any]:
        """
        Load account YAML files and validate bucket security targets.

        Known bucket-target configuration issues are logged as warnings
        during reconciliation. Unexpected errors are allowed to propagate.
        """
        account_dir = os.path.join(
            self.config_dir,
            "accounts",
        )

        if not os.path.exists(account_dir):
            return {}

        accounts: dict[str, AccountConfig] = {}

        for file in os.listdir(account_dir):
            if not file.endswith(".yaml"):
                continue

            key = file.replace(".yaml", "")
            file_path = os.path.join(account_dir, file)

            data = self._load_yaml(file_path)
            account_data = data["account"]

            bucket_mapping = data.get("bucket_mapping") or {}
            bucket_weights = data.get("bucket_weights") or {}
            security_targets = data.get("security_targets") or {}
			
            bucket_tolerance = data["bucket_tolerance"]

            try:
                validate_bucket_security_targets(
                    bucket_mapping=bucket_mapping,
                    bucket_weights=bucket_weights,
                    security_targets=security_targets,
                    bucket_tolerance=bucket_tolerance,
                    account_name=account_data["name"],
                )
            except BucketTargetValidationError as exc:
                logger.warning(
                    "Account '%s' in %s has bucket target "
                    "configuration issues. Loading continues "
                    "temporarily during reconciliation: %s",
                    account_data["name"],
                    file,
                    exc,
                )

            settings_data = data.get(
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

            accounts[key] = AccountConfig(
                name=account_data["name"],
                display_name=account_data["display_name"],
                account_type=account_data["account_type"],
                risk_profile=account_data["risk_profile"],
                account_number=account_data["account_number"],
                institution=account_data["institution"],
                bucket_mapping=bucket_mapping,
                bucket_weights=bucket_weights,
                tolerance=data["tolerance"],
                bucket_tolerance=bucket_tolerance,
                security_targets=security_targets,
                position_limits=PositionLimits(
                    max_position_pct=data.get(
                        "position_limits",
                        {},
                    ).get(
                        "max_position_pct",
                        0.10,
                    ),
                    overrides=data.get(
                        "position_limits",
                        {},
                    ).get(
                        "overrides",
                        {},
                    ),
                ),
                settings=settings,
            )

        return accounts


    # -----------------------------
    # YAML LOADER
    # -----------------------------
    def _load_yaml(self, path: str) -> Dict[str, Any]:
        with open(path, "r") as f:
            return yaml.safe_load(f) or {}

    # -----------------------------
    # LEGACY COMPATIBILITY
    # -----------------------------
    def _inject_legacy_flattened_config(self):
        # Flatten system keys for older tests expecting direct access
        system = self.config.get("system", {})
        for k, v in system.items():
            self.config[k] = v

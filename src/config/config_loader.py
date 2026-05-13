import os
import yaml
from typing import Any, Dict
from pathlib import Path


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
        account_dir = os.path.join(self.config_dir, "accounts")

        if not os.path.exists(account_dir):
            return {}

        accounts = {}

        for file in os.listdir(account_dir):
            if file.endswith(".yaml"):
                key = file.replace(".yaml", "")
                accounts[key] = self._load_yaml(os.path.join(account_dir, file))

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

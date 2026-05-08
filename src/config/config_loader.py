from pathlib import Path
from typing import Any, Dict
import yaml

from src.config.schema_validator import SchemaValidator, ConfigError


class ConfigLoader:
    """
    Responsible ONLY for:
    - locating the config file
    - loading YAML into a dict
    - delegating validation
    """

    def __init__(self, config_path="config/config.yaml"):
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}

    # =========================
    # Public API
    # =========================
    def load(self) -> Dict[str, Any]:
        """
        Load and validate configuration.
        """
        self._validate_file_exists()
        self.config = self._read_yaml()

        validator = SchemaValidator(self.config)
        validator.validate()

        return self.config

    # =========================
    # File Handling
    # =========================
    def _validate_file_exists(self) -> None:
        if not self.config_path.exists():
            raise ConfigError(f"Config file not found: {self.config_path}")

        if not self.config_path.is_file():
            raise ConfigError(f"Path is not a file: {self.config_path}")

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

import logging
import logging.config
from pathlib import Path

import yaml


def setup_logging():
    """
    Configure logging from YAML configuration.
    Should be called once during application startup.
    """

    config_path = (
        Path(__file__).resolve().parents[2] / "src" / "config" / "logging.yaml"
    )

    if not config_path.exists():
        raise FileNotFoundError(f"Logging configuration file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    logging.config.dictConfig(config)


def get_logger(name: str) -> logging.Logger:
    """
    Retrieve a configured logger instance.
    """

    if name != "app" and not name.startswith("app."):
        name = f"app.{name}"
    return logging.getLogger(name)

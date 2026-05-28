import logging
import logging.config
import yaml
from pathlib import Path


def setup_logging(config_path: str):
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    # ensure logs folder exists if file handler used
    Path("logs").mkdir(exist_ok=True)

    logging.config.dictConfig(config)

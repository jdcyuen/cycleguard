import os
from pathlib import Path
from functools import lru_cache

from src.config.config_loader import ConfigLoader


# =========================
# BASE PATH RESOLUTION
# =========================
BASE_DIR = Path(__file__).resolve().parents[2]


# =========================
# ENV → CONFIG MAPPING
# =========================
def _resolve_config_path(env: str) -> str:
    """
    Maps environment name to config file path.
    """

    if env == "test":
        return str(BASE_DIR / "tests/config/test.yaml")

    if env == "prod":
        return str(BASE_DIR / "src/config/prod.yaml")

    # default = dev
    return str(BASE_DIR / "src/config/dev.yaml")


# =========================
# GLOBAL CONFIG LOADER
# =========================
@lru_cache(maxsize=3)
def get_config(env: str | None = None):
    """
    Load CycleGuard config for a given environment.

    Environments:
        - test → unit tests
        - dev  → local Streamlit / development
        - prod → production deployment

    env can also be set via:
        CYCLEGUARD_ENV environment variable
    """

    env = env or os.getenv("CYCLEGUARD_ENV", "dev")

    config_path = _resolve_config_path(env)

    return ConfigLoader(config_path).load()

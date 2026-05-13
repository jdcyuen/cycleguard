import os
from src.config.config_loader import ConfigLoader


# -----------------------------
# Helper: get absolute path
# -----------------------------
def get_test_config_path():
    return os.path.join(os.path.dirname(__file__), "test_config.yaml")


# -----------------------------
# Test 1: Config loads successfully
# -----------------------------
def test_config_load_success():
    loader = ConfigLoader(get_test_config_path())
    config = loader.load()

    assert config is not None
    assert "system" in config
    assert "accounts" in config


# -----------------------------
# Test 2: System has bucket
# -----------------------------
def test_config_has_buckets():
    loader = ConfigLoader(get_test_config_path())
    config = loader.load()

    system = config["system"]

    assert "bucket" in system or "bucket.yaml" in system


# -----------------------------
# Test 3: System has regimes
# -----------------------------
def test_config_has_regimes():
    loader = ConfigLoader(get_test_config_path())
    config = loader.load()

    system = config["system"]

    assert "regime" in system

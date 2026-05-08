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
    assert "portfolio" in config
    assert "regimes" in config


# -----------------------------
# Test 2: Portfolio structure exists
# -----------------------------
def test_config_has_buckets():
    loader = ConfigLoader(get_test_config_path())
    config = loader.load()

    assert "buckets" in config["portfolio"]
    assert isinstance(config["portfolio"]["buckets"], dict)


# -----------------------------
# Test 3: Regimes exist
# -----------------------------
def test_config_has_regimes():
    loader = ConfigLoader(get_test_config_path())
    config = loader.load()

    assert "risk_on" in config["regimes"]
    assert "risk_off" in config["regimes"]

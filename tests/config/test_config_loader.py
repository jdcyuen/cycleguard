import os
from config.config_loader import ConfigLoader
from models.account_config import AccountConfig


# -----------------------------
# Helper: get absolute path
# -----------------------------
def get_test_config_path():
    return os.path.join(os.path.dirname(__file__), "test.yaml")


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


def test_account_bucket_mapping():
    loader = ConfigLoader(get_test_config_path())
    config = loader.load()

    accounts = config["accounts"]

    assert accounts["rollover_ira"].bucket_mapping["FZROX"] == "core_equity"
    assert accounts["rollover_ira"].bucket_mapping["FXNAX"] == "fixed_income"
    assert accounts["rollover_ira"].bucket_mapping["SGOV"] == "defensive"


def test_accounts_are_account_configs():
    loader = ConfigLoader(get_test_config_path())
    config = loader.load()

    accounts = config["accounts"]

    assert isinstance(accounts, dict)
    assert isinstance(accounts["rollover_ira"], AccountConfig)

def test_account_bucket_weights():
    loader = ConfigLoader(get_test_config_path())
    config = loader.load()

    accounts = config["accounts"]

    assert accounts["rollover_ira"].bucket_weights["core_equity"] == 0.20
    assert accounts["rollover_ira"].bucket_weights["fixed_income"] == 0.30


def test_account_position_limits():
    loader = ConfigLoader(get_test_config_path())
    config = loader.load()

    accounts = config["accounts"]

    assert (
        accounts["rollover_ira"]
        .position_limits
        .max_position_pct
        == 0.10
    )

    assert (
        accounts["rollover_ira"]
        .position_limits
        .overrides["FZROX"]
        == 0.20
    )

def test_account_settings():
    loader = ConfigLoader(get_test_config_path())
    config = loader.load()

    accounts = config["accounts"]

    settings = accounts["rollover_ira"].settings

    assert settings.rebalance_frequency == "monthly"
    assert settings.allow_fractional_shares is True
    assert settings.enable_recovery_trims is True
    assert settings.enable_dynamic_deployment is True

def test_accounts_dictionary_contains_account_config():
    loader = ConfigLoader(get_test_config_path())
    config = loader.load()

    accounts = config["accounts"]

    assert isinstance(
        accounts["rollover_ira"],
        AccountConfig,
    )

def test_accounts_contains_account_config_objects():
    loader = ConfigLoader(get_test_config_path())
    config = loader.load()

    accounts = config["accounts"]

    assert isinstance(
        accounts["rollover_ira"],
        AccountConfig,
    )

def test_account_config_contains_bucket_weights():
    loader = ConfigLoader(get_test_config_path())
    config = loader.load()

    account = config["accounts"]["rollover_ira"]

    assert account.bucket_weights["defensive"] == 0.15
    assert account.bucket_weights["fixed_income"] == 0.30
    assert account.bucket_weights["core_equity"] == 0.20

def test_account_config_contains_position_limits():
    loader = ConfigLoader(get_test_config_path())
    config = loader.load()

    account = config["accounts"]["rollover_ira"]

    assert account.position_limits.max_position_pct == 0.10
    assert account.position_limits.overrides["FZROX"] == 0.20
    assert account.position_limits.overrides["SCHD"] == 0.15

def test_account_config_contains_settings():
    loader = ConfigLoader(get_test_config_path())
    config = loader.load()

    account = config["accounts"]["rollover_ira"]

    assert account.settings.rebalance_frequency == "monthly"
    assert account.settings.allow_fractional_shares is True
    assert account.settings.enable_recovery_trims is True
    assert account.settings.enable_dynamic_deployment is True


def test_config_load_returns_account_configs():
    loader = ConfigLoader(get_test_config_path())

    config = loader.load()

    accounts = config["accounts"]

    assert isinstance(accounts, dict)

    for name, account in accounts.items():
        assert isinstance(name, str)
        assert isinstance(account, AccountConfig)


def test_config_load_exposes_rollover_ira_configuration():
    loader = ConfigLoader(get_test_config_path())

    config = loader.load()

    account = config["accounts"]["rollover_ira"]

    assert account.name == "rollover_ira"
    assert account.bucket_weights["core_equity"] == 0.20
    assert account.position_limits.max_position_pct == 0.10
    assert account.position_limits.overrides["FZROX"] == 0.20
    assert account.settings.rebalance_frequency == "monthly"
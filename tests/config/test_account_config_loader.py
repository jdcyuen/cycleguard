# tests/config/test_account_config_loader.py

from pathlib import Path

import pytest

from config.account_config_loader import AccountConfigLoader
from models.account_config import AccountConfig


ACCOUNT_YAML = """
account:
  name: rollover_ira
  display_name: Rollover IRA
  account_type: ira
  risk_profile: conservative
  account_number: "123456"
  institution: Fidelity
"""


@pytest.fixture
def config_dir(tmp_path: Path):
    file = tmp_path / "rollover_ira.yaml"
    file.write_text(ACCOUNT_YAML)
    return tmp_path


def test_load_returns_all_accounts(config_dir):
    loader = AccountConfigLoader(config_dir)

    accounts = loader.load()

    assert len(accounts) == 1

    account = accounts[0]

    assert isinstance(account, AccountConfig)
    assert account.name == "rollover_ira"
    assert account.display_name == "Rollover IRA"
    assert account.account_type == "ira"
    assert account.risk_profile == "conservative"
    assert account.account_number == "123456"
    assert account.institution == "Fidelity"


def test_load_empty_directory_returns_empty_list(tmp_path):
    loader = AccountConfigLoader(tmp_path)

    accounts = loader.load()

    assert accounts == []


def test_load_missing_directory_raises():
    missing = Path("this_directory_should_not_exist")

    loader = AccountConfigLoader(missing)

    with pytest.raises(FileNotFoundError):
        loader.load()


def test_get_existing_account(config_dir):
    loader = AccountConfigLoader(config_dir)

    account = loader.get("rollover_ira")

    assert account is not None
    assert account.name == "rollover_ira"
    assert account.display_name == "Rollover IRA"


def test_get_missing_account_returns_none(tmp_path):
    loader = AccountConfigLoader(tmp_path)

    account = loader.get("does_not_exist")

    assert account is None


def test_load_file_parses_yaml(config_dir):
    loader = AccountConfigLoader(config_dir)

    file = config_dir / "rollover_ira.yaml"

    account = loader._load_file(file)

    assert account == AccountConfig(
        name="rollover_ira",
        display_name="Rollover IRA",
        account_type="ira",
        risk_profile="conservative",
        account_number="123456",
        institution="Fidelity",
    )
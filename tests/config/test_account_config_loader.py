# tests/config/test_account_config_loader.py

from pathlib import Path

import pytest

from config.account_config_loader import AccountConfigLoader
from models.account_config import AccountConfig, PositionLimits, AccountSettings


ACCOUNT_YAML = """
account:
  name: rollover_ira
  display_name: Rollover IRA
  account_type: ira
  risk_profile: conservative
  account_number: "123456"
  institution: Fidelity

bucket_weights:
  defensive: 0.15
  fixed_income: 0.30
  tips_ladder: 0.10
  core_equity: 0.20
  equity_income: 0.10
  equity_growth: 0.07
  high_beta: 0.03
  foreign_equity: 0.03
  alternatives: 0.02
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
         bucket_mapping={},
         bucket_weights={
            "defensive": 0.15,
            "fixed_income": 0.30,
            "tips_ladder": 0.10,
            "core_equity": 0.20,
            "equity_income": 0.10,
            "equity_growth": 0.07,
            "high_beta": 0.03,
            "foreign_equity": 0.03,
            "alternatives": 0.02,
        },
        position_limits=PositionLimits(
            max_position_pct=0.10,
            overrides={},
        ),
        settings=AccountSettings(
            rebalance_frequency="monthly",
            allow_fractional_shares=True,
            enable_recovery_trims=True,
            enable_dynamic_deployment=True,
        ),
    )

def test_bucket_weights_total_100_percent(config_dir):
    loader = AccountConfigLoader(config_dir)
    account = loader.get("rollover_ira")
    assert sum(account.bucket_weights.values()) == pytest.approx(1.0)


def test_bucket_weights_must_total_100_percent(config_dir):
    file = config_dir / "rollover_ira.yaml"

    file.write_text(
    """
account:
  name: rollover_ira
  display_name: Rollover IRA
  account_type: ira
  risk_profile: conservative
  account_number: "123456"
  institution: Fidelity

bucket_weights:
  defensive: 0.50
  fixed_income: 0.30
"""
)

    loader = AccountConfigLoader(config_dir)

    with pytest.raises(
        ValueError,
        match="must total 1.0",
    ):
        loader.get("rollover_ira")

def test_position_limit_must_be_between_zero_and_one(config_dir):
    file = config_dir / "rollover_ira.yaml"

    file.write_text(
        """
account:
  name: rollover_ira
  display_name: Rollover IRA
  account_type: ira
  risk_profile: conservative
  account_number: "123456"
  institution: Fidelity

position_limits:
  max_position_pct: 1.50
"""
    )

    loader = AccountConfigLoader(config_dir)

    with pytest.raises(
        ValueError,
        match="must be between 0 and 1.0",
    ):
        loader.get("rollover_ira")


def test_position_limit_override_must_be_between_zero_and_one(
    config_dir,
):
    file = config_dir / "rollover_ira.yaml"

    file.write_text(
        """
account:
  name: rollover_ira
  display_name: Rollover IRA
  account_type: ira
  risk_profile: conservative
  account_number: "123456"
  institution: Fidelity

position_limits:
  max_position_pct: 0.10
  overrides:
    FZROX: 1.50
"""
    )

    loader = AccountConfigLoader(config_dir)

    with pytest.raises(
        ValueError,
        match="Position limit for FZROX",
    ):
        loader.get("rollover_ira")


def test_account_config_exposes_complete_configuration(config_dir):
    file = config_dir / "rollover_ira.yaml"

    file.write_text(
        """
account:
  name: rollover_ira
  display_name: Rollover IRA
  account_type: ira
  risk_profile: conservative
  account_number: "123456"
  institution: Fidelity

bucket_mapping:
  FZROX: core_equity

bucket_weights:
  defensive: 0.15
  fixed_income: 0.30
  tips_ladder: 0.10
  core_equity: 0.20
  equity_income: 0.10
  equity_growth: 0.07
  high_beta: 0.03
  foreign_equity: 0.03
  alternatives: 0.02

position_limits:
  max_position_pct: 0.10
  overrides:
    FZROX: 0.20

settings:
  rebalance_frequency: monthly
  allow_fractional_shares: true
  enable_recovery_trims: true
  enable_dynamic_deployment: true
"""
    )

    loader = AccountConfigLoader(config_dir)

    account = loader.get("rollover_ira")

    assert account.name == "rollover_ira"
    assert account.bucket_mapping == {
        "FZROX": "core_equity",
    }

    assert account.bucket_weights["core_equity"] == 0.20

    assert account.position_limits.max_position_pct == 0.10
    assert account.position_limits.overrides["FZROX"] == 0.20

    assert account.settings.rebalance_frequency == "monthly"
    assert account.settings.allow_fractional_shares is True
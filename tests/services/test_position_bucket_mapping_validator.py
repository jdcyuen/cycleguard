from types import SimpleNamespace

import pandas as pd
import pytest
import yaml

from services.position_bucket_mapping_validator import (
    PositionBucketMappingValidator,
)


@pytest.fixture
def validator_setup(tmp_path):
    project_root = tmp_path
    system_dir = project_root / "src" / "config" / "system"
    accounts_dir = project_root / "src" / "config" / "accounts"
    system_dir.mkdir(parents=True)
    accounts_dir.mkdir(parents=True)

    (system_dir / "buckets.yaml").write_text(
        yaml.safe_dump(
            {
                "buckets": [
                    "defensive",
                    "fixed_income",
                    "tips_ladder",
                    "equity_income",
                    "core_equity",
                    "equity_growth",
                    "high_beta",
                    "foreign_equity",
                    "alternatives",
                ]
            }
        ),
        encoding="utf-8",
    )

    account_config = SimpleNamespace(
        name="rollover_ira",
        display_name="Rollover IRA",
        bucket_mapping={
            "FZROX": "core_equity",
            "FDRXX": "defensive",
        },
    )

    account_yaml = accounts_dir / "rollover_ira.yaml"
    account_yaml.write_text("bucket_mapping: {}\n", encoding="utf-8")

    loader = SimpleNamespace(load=lambda: [account_config])
    validator = PositionBucketMappingValidator(
        account_config_loader=loader,
        project_root=project_root,
    )
    account = SimpleNamespace(name="Rollover IRA")

    return validator, account, account_config, account_yaml


def test_all_symbols_mapped_returns_no_warnings(validator_setup):
    validator, account, _, _ = validator_setup
    dataframe = pd.DataFrame({"symbol": ["FZROX", "FDRXX"]})

    assert validator.validate(dataframe, account) == []


def test_unmapped_symbols_report_account_yaml_path(validator_setup):
    validator, account, _, account_yaml = validator_setup
    dataframe = pd.DataFrame({"symbol": ["FZROX", "UNKNOWN"]})

    warnings = validator.validate(dataframe, account)

    assert len(warnings) == 1
    assert "UNKNOWN" in warnings[0]
    assert "Assign each symbol to a valid bucket" in warnings[0]
    assert "src/config/system/buckets.yaml" in warnings[0]
    normalized_warning = warnings[0].replace(chr(92), "/")
    assert "src/config/accounts/rollover_ira.yaml" in normalized_warning


def test_invalid_bucket_name_is_rejected(validator_setup):
    validator, account, account_config, account_yaml = validator_setup
    account_config.bucket_mapping["FZROX"] = "invalid_bucket"
    dataframe = pd.DataFrame({"symbol": ["FZROX"]})

    with pytest.raises(ValueError, match="Invalid bucket name"):
        validator.validate(dataframe, account)

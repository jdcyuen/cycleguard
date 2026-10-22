from pathlib import Path

import pandas as pd
import yaml

from config.account_config_loader import AccountConfigLoader


class PositionBucketMappingValidator:
    """Validate position symbols against an account's YAML bucket mapping."""


    def __init__(
        self,
        account_config_loader: AccountConfigLoader | None = None,
        project_root: Path | None = None,
    ):
        self._account_config_loader = (
            account_config_loader or AccountConfigLoader()
        )
        self._project_root = (
            Path(project_root)
            if project_root is not None
            else Path(__file__).resolve().parents[2]
        )
        self._buckets_path = (
            self._project_root / "src" / "config" / "system" / "buckets.yaml"
        )

    def validate(self, dataframe, account) -> list[str]:
        """Return warnings for unmapped symbols; reject invalid bucket names."""
        account_name = str(account.name).strip()
        configs = self._account_config_loader.load()

        matching_configs = [
            config
            for config in configs
            if config.display_name.casefold() == account_name.casefold()
            or config.name.casefold() == account_name.casefold()
        ]

        if len(matching_configs) != 1:
            raise ValueError(
                f"Could not uniquely match account '{account_name}' "
                "to an account YAML configuration."
            )

        account_config = matching_configs[0]
        account_yaml = (
            self._project_root
            / "src"
            / "config"
            / "accounts"
            / f"{account_config.name}.yaml"
        )

        with self._buckets_path.open("r", encoding="utf-8") as stream:
            bucket_data = yaml.safe_load(stream) or {}

        valid_buckets = set(bucket_data.get("buckets", []))
        invalid_buckets = sorted(
            {
                bucket
                for bucket in account_config.bucket_mapping.values()
                if bucket not in valid_buckets
            }
        )

        if invalid_buckets:
            raise ValueError(
                f"Invalid bucket name(s) in {account_yaml}: "
                f"{', '.join(invalid_buckets)}. "
                f"Valid buckets are: {', '.join(sorted(valid_buckets))}."
            )

        if "symbol" not in dataframe.columns:
            raise ValueError(
                "Cannot validate account bucket mapping: "
                "the positions CSV has no 'symbol' column."
            )

        csv_symbols = {
            str(symbol).strip().upper()
            for symbol in dataframe["symbol"].dropna()
            if str(symbol).strip()
        }
        mapped_symbols = {
            str(symbol).strip().upper()
            for symbol in account_config.bucket_mapping
        }
        unmapped_symbols = sorted(csv_symbols - mapped_symbols)

        if not unmapped_symbols:
            return []

        warning = (
            f"Unmapped symbols for account '{account_name}': "
            f"{', '.join(unmapped_symbols)}. "
            f"Add them under bucket_mapping in {account_yaml.relative_to(self._project_root)}."
        )

        warning += (
            " Assign each symbol to a valid bucket in "
            f"{account_yaml.relative_to(self._project_root)}. "
            "Valid buckets are defined in "
            "src/config/system/buckets.yaml."
        )

        return [warning]

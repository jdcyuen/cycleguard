
"""
Module: Account Configuration Loader
=====================================

Purpose
-------
Load, validate, and construct account configuration objects from the
YAML files stored in src/config/accounts.

The loader provides a consistent interface for retrieving account
configuration independently of portfolio calculations, market data,
database access, dashboard presentation, and trade execution.

Architecture
------------
This module belongs to CycleGuard's configuration layer.

    Account YAML files
          |
          v
    AccountConfigLoader
          |
          +---- Read and parse YAML
          |
          +---- Validate basic configuration structure
          |
          +---- Validate bucket/security target consistency
          |          |
          |          v
          |    BucketTargetValidator
          |
          +---- Construct AccountConfig objects
                     |
                     v
              AccountConfig
                     |
          +----------+-----------+
          |          |           |
          v          v           v
     Portfolio   Deployment   Reconciliation
       View       Services      Services

Responsibilities
----------------
1. Locate account configuration files.
2. Read and parse account YAML.
3. Extract account metadata and configuration settings.
4. Validate basic configuration values.
5. Invoke the shared BucketTargetValidator for bucket/security
   target consistency.
6. Construct and return AccountConfig objects.
7. Log configuration loading activity and failures.

Design Principles
-----------------
Single Responsibility:
    This class handles account configuration loading and construction.
    Bucket/security target consistency rules remain in the dedicated
    BucketTargetValidator.

Open/Closed:
    New account settings and validation rules should be added through
    their appropriate configuration models and validation components,
    rather than embedding unrelated business logic here.

Dependency Inversion:
    The loader depends on the AccountConfig model and the public
    validation interface, not on portfolio or trading services.

Separation of Concerns:
    YAML access, configuration validation, portfolio analysis,
    allocation calculations, and trade execution remain separate.

Public Interface
----------------
load():
    Load every YAML account configuration in the configured directory.
    Returns a list of AccountConfig objects.

get(account_name):
    Load one account configuration by its YAML filename.
    Returns AccountConfig or None when the file does not exist.

_load_file(file):
    Internal method that parses, validates, and constructs one
    AccountConfig object.

Validation Policy
-----------------
The shared BucketTargetValidator checks:

    - Bucket tolerance.
    - Security targets without bucket mappings.
    - Bucket mappings without security targets.
    - Mappings to unknown buckets.
    - Invalid security target and bucket weight values.
    - Differences between bucket weights and security target totals.

A BucketTargetValidationError is logged as a warning. Loading continues
temporarily to preserve the existing reconciliation behavior.

Other configuration errors are not suppressed. They are logged with
their traceback and propagated to the caller.

The loader also verifies that configured bucket weights total 1.0 and
that position limits are within their permitted ranges.

Error Handling
--------------
FileNotFoundError:
    The account directory or requested account file is unavailable.

PermissionError:
    The process cannot access a configuration file.

yaml.YAMLError:
    The YAML document cannot be parsed.

KeyError:
    A required configuration field is missing.

TypeError / ValueError:
    Configuration data has an invalid structure or value.

Unexpected exceptions:
    Logged with traceback and re-raised.

Missing account lookup:
    Logged as a warning and returns None. This is an expected lookup
    outcome, not a configuration-loading failure.

Logging
-------
INFO:
    Account loading begins and completes successfully.

DEBUG:
    Individual account files are processed.

WARNING:
    An account file is missing during lookup or has a known
    bucket/security target validation issue.

ERROR:
    Configuration loading fails. The exception and traceback are
    retained in the application log.

Integration
-----------
AccountConfigLoader is used by CycleGuard components that require
structured account configuration.

It constructs AccountConfig objects but does not calculate actual
portfolio allocations, determine deployment amounts, select securities,
or execute trades.

Portfolio View consumes the resulting AccountConfig to construct
configured target allocations independently of actual account holdings.

Important
---------
Successful loading does not establish that an investment allocation
is financially appropriate or that actual holdings match configured
targets. Those responsibilities belong to downstream analysis and
validation components.
"""

import math
from pathlib import Path

import yaml

from config.bucket_target_validator import (
    BucketTargetValidationError,
    validate_bucket_security_targets,
)
from core.logger import get_logger
from models.account_config import (
    AccountConfig,
    AccountSettings,
    PositionLimits,
)

logger = get_logger(__name__)


class AccountConfigLoader:
    """
    Load and construct account configurations from YAML files.

    Args:
        config_dir: Optional directory containing account YAML files.
            Defaults to src/config/accounts.
    """

    def __init__(
        self,
        config_dir: Path | None = None,
    ) -> None:
        self._config_dir = (
            Path(config_dir)
            if config_dir is not None
            else Path(__file__).resolve().parent / "accounts"
        )

    def load(self) -> list[AccountConfig]:
        """
        Load all account configurations.

        Returns:
            A list of successfully constructed AccountConfig objects.

        Raises:
            FileNotFoundError: If the configuration directory is missing.
            PermissionError: If the directory cannot be accessed.
            Exception: If an account configuration cannot be loaded.
        """
        logger.info(
            "Loading account configurations from '%s'.",
            self._config_dir,
        )

        if not self._config_dir.exists():
            raise FileNotFoundError(
                f"Account configuration directory not found: "
                f"{self._config_dir}"
            )

        if not self._config_dir.is_dir():
            raise NotADirectoryError(
                f"Account configuration path is not a directory: "
                f"{self._config_dir}"
            )

        files = sorted(self._config_dir.glob("*.yaml"))

        accounts = [
            self._load_file(file)
            for file in files
        ]

        logger.info(
            "Successfully loaded %d account configuration(s).",
            len(accounts),
        )

        return accounts

    def get(
        self,
        account_name: str,
    ) -> AccountConfig | None:
        """
        Load one account configuration by account name.

        Args:
            account_name: Account identifier corresponding to a YAML
                filename without its extension.

        Returns:
            AccountConfig when found; otherwise None.

        Raises:
            Exception: If the account file exists but cannot be loaded.
        """
        if not account_name or Path(account_name).name != account_name:
            raise ValueError(
                f"Invalid account name: {account_name!r}"
            )

        file = self._config_dir / f"{account_name}.yaml"

        if not file.exists():
            logger.warning(
                "Account configuration not found: '%s'.",
                account_name,
            )
            return None

        logger.info(
            "Loading account configuration for '%s'.",
            account_name,
        )

        return self._load_file(file)

    def _load_file(
        self,
        file: Path,
    ) -> AccountConfig:
        """
        Parse, validate, and construct one account configuration.

        Known bucket/security target validation failures are logged as
        warnings to preserve existing reconciliation behavior.
        Other failures are logged and propagated.

        Args:
            file: Path to the account YAML file.

        Returns:
            A constructed AccountConfig object.

        Raises:
            Exception: If reading, parsing, validation, or construction
                fails outside the tolerated bucket-target warning.
        """
        logger.debug(
            "Processing account configuration file '%s'.",
            file.name,
        )

        try:
            with file.open(
                "r",
                encoding="utf-8",
            ) as stream:
                config = yaml.safe_load(stream)

            account = config["account"]

            bucket_mapping = config.get("bucket_mapping") or {}
            bucket_weights = config.get("bucket_weights") or {}
            security_targets = config.get("security_targets") or {}

            tolerance = config["tolerance"]
            bucket_tolerance = config["bucket_tolerance"]

            # Validate the total configured bucket allocation.
            if bucket_weights and not math.isclose(
                sum(bucket_weights.values()),
                1.0,
                rel_tol=0.0,
                abs_tol=1e-9,
            ):
                raise ValueError(
                    f"Bucket weights for {file.name} must total 1.0"
                )

            # Delegate bucket/security consistency validation to the
            # dedicated validator. Do not duplicate its business rules.
            try:
                validate_bucket_security_targets(
                    bucket_mapping=bucket_mapping,
                    bucket_weights=bucket_weights,
                    security_targets=security_targets,
                    bucket_tolerance=bucket_tolerance,
                    account_name=account["name"],
                )
            except BucketTargetValidationError as exc:
                logger.warning(
                    "Account '%s' in %s has bucket target "
                    "configuration issues. Loading continues "
                    "temporarily during reconciliation: %s",
                    account["name"],
                    file.name,
                    exc,
                )

            # Load and validate position limits.
            position_limits_data = config.get(
                "position_limits",
                {},
            )

            max_position_pct = position_limits_data.get(
                "max_position_pct",
                0.10,
            )

            overrides = position_limits_data.get(
                "overrides",
                {},
            )

            if (
                not isinstance(max_position_pct, (int, float))
                or isinstance(max_position_pct, bool)
                or not math.isfinite(max_position_pct)
                or not 0 <= max_position_pct <= 1.0
            ):
                raise ValueError(
                    f"Default position limit for {file.name} "
                    "must be between 0 and 1.0 and finite"
                )

            for symbol, limit in overrides.items():
                if (
                    not isinstance(limit, (int, float))
                    or isinstance(limit, bool)
                    or not math.isfinite(limit)
                    or not 0 <= limit <= 1.0
                ):
                    raise ValueError(
                        f"Position limit for {symbol} in {file.name} "
                        "must be between 0 and 1.0 and finite"
                    )

            position_limits = PositionLimits(
                max_position_pct=max_position_pct,
                overrides=overrides,
            )

            # Load account-level operational settings.
            settings_data = config.get(
                "settings",
                {},
            )

            settings = AccountSettings(
                rebalance_frequency=settings_data.get(
                    "rebalance_frequency",
                    "monthly",
                ),
                allow_fractional_shares=settings_data.get(
                    "allow_fractional_shares",
                    True,
                ),
                enable_recovery_trims=settings_data.get(
                    "enable_recovery_trims",
                    True,
                ),
                enable_dynamic_deployment=settings_data.get(
                    "enable_dynamic_deployment",
                    True,
                ),
            )

            account_config = AccountConfig(
                name=account["name"],
                display_name=account["display_name"],
                account_type=account["account_type"],
                risk_profile=account["risk_profile"],
                account_number=account["account_number"],
                institution=account["institution"],
                bucket_mapping=bucket_mapping,
                bucket_weights=bucket_weights,
                tolerance=tolerance,
                bucket_tolerance=bucket_tolerance,
                security_targets=security_targets,
                position_limits=position_limits,
                settings=settings,
                config_path=str(file.resolve()),
            )

            logger.info(
                "Successfully loaded account '%s' from '%s'.",
                account_config.name,
                file.name,
            )

            return account_config

        except Exception:
            logger.exception(
                "Failed to load account configuration from '%s'.",
                file,
            )
            raise

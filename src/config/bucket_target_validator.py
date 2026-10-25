
"""
Module: Bucket Security Target Validator
========================================

Purpose
-------
Validate the consistency of an account's bucket allocation configuration
before CycleGuard relies on it for portfolio analysis or trade proposals.

Architecture
------------
This module belongs to the configuration-validation layer:

    Account YAML files
          |
          v
    Configuration loaders
          |
          v
    Bucket Security Target Validator
          |
          v
    Validated account configuration
          |
          v
    Portfolio aggregation / allocation analysis / trade proposals

The validator is deliberately independent of YAML file access, databases,
market data, dashboards, and trade execution. It receives configuration
values from its caller and validates their internal consistency.

Validation rules
----------------
1. Bucket tolerance must be a finite number between 0.0 and 1.0.
2. Every security with a target must have a bucket mapping.
3. Every mapped security must have a security target.
4. Every mapped bucket must exist in bucket_weights.
5. Security targets and bucket weights must be finite numbers between
   0.0 and 1.0.
6. For each bucket, the sum of its mapped security targets must equal
   the configured bucket weight within bucket_tolerance.

The comparison uses absolute tolerance because the configuration values
represent portfolio-weight fractions. For example, a tolerance of 0.02
permits a difference of two percentage points, not two percent of the
bucket weight.

Inputs
------
bucket_mapping:
    Mapping of security symbols to canonical CycleGuard bucket names.

bucket_weights:
    Mapping of bucket names to target portfolio-weight fractions.

security_targets:
    Mapping of security symbols to target portfolio-weight fractions.

bucket_tolerance:
    Maximum permitted absolute difference between a bucket's target
    weight and the sum of its security targets.

account_name:
    Account identifier included in log messages and validation errors.

Behavior
--------
The public function returns None when validation succeeds.

Invalid configuration raises ValueError with a descriptive message.
Unexpected errors are logged with their traceback and re-raised.
Exceptions are never silently suppressed.

Logging
-------
INFO:
    Validation start and successful completion.

ERROR:
    Invalid configuration or unexpected validation failure.

Integration
-----------
Configuration loaders should invoke this validator after reading the
account's bucket_mapping, bucket_weights, security_targets, and
bucket_tolerance values, and before returning the AccountConfig.

Both current account-loading paths should use the same validation
function to avoid inconsistent validation behavior.

The validator does not modify allocation targets or infer missing
mappings. Configuration corrections remain an explicit operator decision.

Important
---------
A successful validation confirms consistency between the supplied
configuration values. It does not establish that the allocations are
financially appropriate, that the holdings match the configuration, or
that a proposed trade is suitable for execution.
"""

import math
from collections.abc import Mapping
from numbers import Real

from core.logger import get_logger

logger = get_logger(__name__)


class BucketTargetValidationError(ValueError):
    """Raised when account bucket targets are invalid or inconsistent."""


def _validate_weight(
    value: object,
    description: str,
) -> None:
    """Require a finite numeric portfolio-weight fraction."""
    if (
        not isinstance(value, Real)
        or isinstance(value, bool)
        or not math.isfinite(value)
        or not 0.0 <= value <= 1.0
    ):
        raise BucketTargetValidationError(
            f"{description} must be a finite number "
            "between 0.0 and 1.0"
        )


def validate_bucket_security_targets(
    bucket_mapping: Mapping[str, str],
    bucket_weights: Mapping[str, float],
    security_targets: Mapping[str, float],
    bucket_tolerance: float,
    account_name: str,
) -> None:
    """
    Validate security targets against configured bucket weights.

    Raises:
        ValueError: If the configuration is invalid or inconsistent.
        TypeError: If an input is not a supported mapping.
        Exception: Unexpected errors are logged and propagated.
    """
    logger.info(
        "Starting bucket security target validation for account '%s'.",
        account_name,
    )

    try:
        mappings = (
            ("bucket_mapping", bucket_mapping),
            ("bucket_weights", bucket_weights),
            ("security_targets", security_targets),
        )

        for name, value in mappings:
            if not isinstance(value, Mapping):
                raise TypeError(
                    f"{name} for account '{account_name}' "
                    "must be a mapping"
                )

        _validate_weight(
            bucket_tolerance,
            f"Bucket tolerance for account '{account_name}'",
        )

        # Check bucket weights before performing any calculations.
        for bucket, weight in bucket_weights.items():
            _validate_weight(
                weight,
                f"Bucket weight for '{bucket}' "
                f"in account '{account_name}'",
            )

        # Check security targets before aggregating them.
        for symbol, target in security_targets.items():
            _validate_weight(
                target,
                f"Security target for '{symbol}' "
                f"in account '{account_name}'",
            )

        # Every target must have an explicit bucket assignment.
        unmapped_targets = sorted(
            symbol
            for symbol in security_targets
            if symbol not in bucket_mapping
        )

        if unmapped_targets:
            raise BucketTargetValidationError(
                f"Unmapped security targets for account "
                f"'{account_name}': {', '.join(unmapped_targets)}"
            )

        # Every mapped security must have a target.
        missing_targets = sorted(
            symbol
            for symbol in bucket_mapping
            if symbol not in security_targets
        )

        if missing_targets:
            raise BucketTargetValidationError(
                f"Mapped securities without targets for account "
                f"'{account_name}': {', '.join(missing_targets)}"
            )

        # Every mapping must refer to a configured canonical bucket.
        unknown_buckets = sorted(
            {
                bucket
                for bucket in bucket_mapping.values()
                if bucket not in bucket_weights
            }
        )

        if unknown_buckets:
            raise BucketTargetValidationError(
                f"Mapped buckets missing from bucket_weights for "
                f"account '{account_name}': "
                f"{', '.join(unknown_buckets)}"
            )

        # Validate each bucket's security-target subtotal.
        for bucket, bucket_weight in bucket_weights.items():
            target_total = math.fsum(
                security_targets[symbol]
                for symbol, mapped_bucket in bucket_mapping.items()
                if mapped_bucket == bucket
            )

            difference = target_total - bucket_weight

            if abs(difference) > bucket_tolerance:
                raise BucketTargetValidationError(
                    f"Security targets for bucket '{bucket}' "
                    f"in account '{account_name}' total "
                    f"{target_total:.2%}, but bucket weight is "
                    f"{bucket_weight:.2%}; difference is "
                    f"{difference:+.2%}, exceeding tolerance of "
                    f"{bucket_tolerance:.2%}"
                )

    except BucketTargetValidationError:
        logger.warning(
            "Bucket security target validation failed for account '%s'.",
            account_name,
        )
        raise

    except Exception:
        logger.exception(
            "Unexpected error during bucket security target validation "
            "for account '%s'.",
            account_name,
        )
        raise

    logger.info(
        "Bucket security target validation passed for account '%s'.",
        account_name,
    )

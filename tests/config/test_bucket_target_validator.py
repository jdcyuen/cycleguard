
import pytest

from config.bucket_target_validator import (
    validate_bucket_security_targets,
)


def test_valid_bucket_targets_match_bucket_weights():
    bucket_mapping = {
        "FDRXX": "defensive",
        "SGOV": "defensive",
        "FZROX": "core_equity",
    }
    bucket_weights = {
        "defensive": 0.15,
        "core_equity": 0.12,
    }
    security_targets = {
        "FDRXX": 0.10,
        "SGOV": 0.05,
        "FZROX": 0.12,
    }

    validate_bucket_security_targets(
        bucket_mapping=bucket_mapping,
        bucket_weights=bucket_weights,
        security_targets=security_targets,
        bucket_tolerance=0.02,
        account_name="test_account",
    )


def test_bucket_target_mismatch_raises_value_error():
    bucket_mapping = {
        "FDRXX": "defensive",
        "SGOV": "defensive",
    }
    bucket_weights = {
        "defensive": 0.13,
    }
    security_targets = {
        "FDRXX": 0.10,
        "SGOV": 0.05,
    }

    with pytest.raises(
        ValueError,
        match="defensive",
    ):
        validate_bucket_security_targets(
            bucket_mapping=bucket_mapping,
            bucket_weights=bucket_weights,
            security_targets=security_targets,
            bucket_tolerance=0.01,
            account_name="test_account",
        )


def test_unmapped_security_target_raises_value_error():
    bucket_mapping = {
        "FDRXX": "defensive",
    }
    bucket_weights = {
        "defensive": 0.10,
    }
    security_targets = {
        "FDRXX": 0.10,
        "IBIC": 0.02,
    }

    with pytest.raises(
        ValueError,
        match="IBIC",
    ):
        validate_bucket_security_targets(
            bucket_mapping=bucket_mapping,
            bucket_weights=bucket_weights,
            security_targets=security_targets,
            bucket_tolerance=0.02,
            account_name="test_account",
        )

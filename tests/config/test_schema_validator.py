import pytest

from config.schema_validator import (
    ConfigError,
    SchemaValidator,
    validate_config,
)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def valid_config():
    return {
        "portfolio": {
            "buckets": {
                "growth": ["SCHG", "QQQM"],
                "income": ["JEPI"],
                "defensive": {
                    "cash_like": ["SGOV"],
                    "bonds": ["BINC"],
                },
            }
        },
        "regimes": {
            "bull": {
                "growth": 0.60,
                "income": 0.20,
                "defensive": {
                    "cash_like": 0.10,
                    "bonds": 0.10,
                },
            }
        },
    }


# ------------------------------------------------------------------
# validate()
# ------------------------------------------------------------------

def test_validate_success():
    validator = SchemaValidator(valid_config())

    validator.validate()


def test_validate_config_function():
    validate_config(valid_config())


# ------------------------------------------------------------------
# Top-level validation
# ------------------------------------------------------------------

def test_missing_portfolio_key():
    cfg = valid_config()
    del cfg["portfolio"]

    with pytest.raises(ConfigError, match="Missing required top-level key"):
        SchemaValidator(cfg).validate()


def test_missing_regimes_key():
    cfg = valid_config()
    del cfg["regimes"]

    with pytest.raises(ConfigError, match="Missing required top-level key"):
        SchemaValidator(cfg).validate()


# ------------------------------------------------------------------
# Bucket validation
# ------------------------------------------------------------------

def test_missing_buckets():
    cfg = valid_config()
    cfg["portfolio"] = {}

    with pytest.raises(ConfigError, match="Missing 'portfolio.buckets' section"):
        SchemaValidator(cfg).validate()


def test_buckets_not_dict():
    cfg = valid_config()
    cfg["portfolio"]["buckets"] = []

    with pytest.raises(ConfigError, match="'portfolio.buckets' must be a dictionary"):
        SchemaValidator(cfg).validate()


def test_bucket_not_list():
    cfg = valid_config()
    cfg["portfolio"]["buckets"]["growth"] = "SCHG"

    with pytest.raises(ConfigError, match="growth must be a list"):
        SchemaValidator(cfg).validate()


def test_empty_bucket():
    cfg = valid_config()
    cfg["portfolio"]["buckets"]["growth"] = []

    with pytest.raises(ConfigError, match="growth cannot be empty"):
        SchemaValidator(cfg).validate()


def test_invalid_symbol_type():
    cfg = valid_config()
    cfg["portfolio"]["buckets"]["growth"] = ["SCHG", 123]

    with pytest.raises(ConfigError, match="Invalid symbol"):
        SchemaValidator(cfg).validate()


def test_nested_bucket_not_list():
    cfg = valid_config()
    cfg["portfolio"]["buckets"]["defensive"]["cash_like"] = "SGOV"

    with pytest.raises(ConfigError, match="defensive.cash_like must be a list"):
        SchemaValidator(cfg).validate()


# ------------------------------------------------------------------
# Regime validation
# ------------------------------------------------------------------

def test_regimes_not_dict():
    cfg = valid_config()
    cfg["regimes"] = []

    with pytest.raises(ConfigError, match="'regimes' must be a dictionary"):
        SchemaValidator(cfg).validate()


def test_regime_not_dict():
    cfg = valid_config()
    cfg["regimes"]["bull"] = []

    with pytest.raises(ConfigError, match="Regime 'bull' must be a dictionary"):
        SchemaValidator(cfg).validate()


def test_weight_not_numeric():
    cfg = valid_config()
    cfg["regimes"]["bull"]["growth"] = "high"

    with pytest.raises(ConfigError, match="Weight must be numeric"):
        SchemaValidator(cfg).validate()


def test_weight_less_than_zero():
    cfg = valid_config()
    cfg["regimes"]["bull"]["growth"] = -0.1

    with pytest.raises(ConfigError, match="Weight must be between 0 and 1"):
        SchemaValidator(cfg).validate()


def test_weight_greater_than_one():
    cfg = valid_config()
    cfg["regimes"]["bull"]["growth"] = 1.2

    with pytest.raises(ConfigError, match="Weight must be between 0 and 1"):
        SchemaValidator(cfg).validate()


def test_weights_do_not_sum_to_one():
    cfg = valid_config()

    cfg["regimes"]["bull"] = {
        "growth": 0.50,
        "income": 0.20,
        "defensive": {
            "cash_like": 0.10,
            "bonds": 0.10,
        },
    }

    with pytest.raises(ConfigError, match="weights must sum"):
        SchemaValidator(cfg).validate()


# ------------------------------------------------------------------
# Duplicate symbols
# ------------------------------------------------------------------

def test_duplicate_symbol_same_level():
    cfg = valid_config()
    cfg["portfolio"]["buckets"]["income"].append("SCHG")

    with pytest.raises(ConfigError, match="Duplicate symbol 'SCHG'"):
        SchemaValidator(cfg).validate()


def test_duplicate_symbol_nested_bucket():
    cfg = valid_config()
    cfg["portfolio"]["buckets"]["defensive"]["cash_like"].append("JEPI")

    with pytest.raises(ConfigError, match="Duplicate symbol 'JEPI'"):
        SchemaValidator(cfg).validate()


# ------------------------------------------------------------------
# Direct helper coverage
# ------------------------------------------------------------------

def test_check_duplicate_first_occurrence():
    validator = SchemaValidator(valid_config())

    symbol_map = {}

    validator._check_duplicate(
        "SCHG",
        "growth",
        None,
        symbol_map,
    )

    assert symbol_map["SCHG"] == ("growth", None)


def test_check_duplicate_raises():
    validator = SchemaValidator(valid_config())

    symbol_map = {
        "SCHG": ("growth", None)
    }

    with pytest.raises(ConfigError, match="Duplicate symbol 'SCHG'"):
        validator._check_duplicate(
            "SCHG",
            "income",
            None,
            symbol_map,
        )
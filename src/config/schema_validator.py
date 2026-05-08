from typing import Any, Dict, Tuple


class ConfigError(Exception):
    """Custom exception for schema validation errors."""

    pass


class SchemaValidator:
    def __init__(self, config: Dict[str, Any]):
        self.config = config

    # =========================
    # Public Entry Point
    # =========================
    def validate(self) -> None:
        self._validate_top_level_keys()
        self._validate_buckets()
        self._validate_regimes()
        self._validate_no_duplicate_symbols()

    # =========================
    # Top-Level Validation
    # =========================
    def _validate_top_level_keys(self):
        required_keys = ["portfolio", "regimes"]

        for key in required_keys:
            if key not in self.config:
                raise ConfigError(f"Missing required top-level key: '{key}'")

    # =========================
    # Bucket Validation
    # =========================
    def _validate_buckets(self):
        buckets = self.config.get("portfolio", {}).get("buckets")

        if not buckets:
            raise ConfigError("Missing 'portfolio.buckets' section")

        if not isinstance(buckets, dict):
            raise ConfigError("'portfolio.buckets' must be a dictionary")

        for bucket_name, value in buckets.items():
            if isinstance(value, dict):
                # Nested bucket (e.g., defensive.cash_like)
                for sub_name, symbols in value.items():
                    self._validate_symbol_list(symbols, f"{bucket_name}.{sub_name}")
            else:
                self._validate_symbol_list(value, bucket_name)

    def _validate_symbol_list(self, symbols: Any, context: str):
        if not isinstance(symbols, list):
            raise ConfigError(f"{context} must be a list of symbols")

        if len(symbols) == 0:
            raise ConfigError(f"{context} cannot be empty")

        for symbol in symbols:
            if not isinstance(symbol, str):
                raise ConfigError(f"Invalid symbol '{symbol}' in {context}")

    # =========================
    # Regime Validation
    # =========================
    def _validate_regimes(self):
        regimes = self.config.get("regimes")

        if not regimes:
            raise ConfigError("Missing 'regimes' section")

        if not isinstance(regimes, dict):
            raise ConfigError("'regimes' must be a dictionary")

        for regime_name, allocations in regimes.items():
            if not isinstance(allocations, dict):
                raise ConfigError(f"Regime '{regime_name}' must be a dictionary")

            self._validate_regime_weights(regime_name, allocations)

    def _validate_regime_weights(self, regime_name: str, allocations: Dict[str, Any]):
        total_weight = 0.0

        for bucket, value in allocations.items():
            if isinstance(value, dict):
                for sub_bucket, weight in value.items():
                    self._validate_weight(
                        weight, f"{regime_name}.{bucket}.{sub_bucket}"
                    )
                    total_weight += weight
            else:
                self._validate_weight(value, f"{regime_name}.{bucket}")
                total_weight += value

        # Allow tolerance for floating point math
        if not (0.99 <= total_weight <= 1.01):
            raise ConfigError(
                f"Regime '{regime_name}' weights must sum to ~1.0 "
                f"(got {total_weight:.4f})"
            )

    def _validate_weight(self, weight: Any, context: str):
        if not isinstance(weight, (int, float)):
            raise ConfigError(f"Weight must be numeric in {context}")

        if weight < 0 or weight > 1:
            raise ConfigError(f"Weight must be between 0 and 1 in {context}")

    # =========================
    # Duplicate Detection
    # =========================
    def _validate_no_duplicate_symbols(self):
        symbol_map: Dict[str, Tuple[str, str]] = {}
        buckets = self.config["portfolio"]["buckets"]

        for bucket_name, value in buckets.items():
            if isinstance(value, dict):
                for sub_name, symbols in value.items():
                    for symbol in symbols:
                        self._check_duplicate(symbol, bucket_name, sub_name, symbol_map)
            else:
                for symbol in value:
                    self._check_duplicate(symbol, bucket_name, None, symbol_map)

    def _check_duplicate(
        self,
        symbol: str,
        bucket: str,
        sub_bucket: str,
        symbol_map: Dict[str, Tuple[str, str]],
    ):
        if symbol in symbol_map:
            prev_bucket, prev_sub = symbol_map[symbol]

            raise ConfigError(
                f"Duplicate symbol '{symbol}' found in "
                f"{prev_bucket}.{prev_sub} and {bucket}.{sub_bucket}"
            )

        symbol_map[symbol] = (bucket, sub_bucket)

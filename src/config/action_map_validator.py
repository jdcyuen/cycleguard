"""
Module: Transaction Action-Map Configuration Validator
=====================================================

Purpose
-------
Validate the structure and contents of the transaction action-map
configuration before CycleGuard uses it to normalize transaction actions
or validate transaction purposes.

Architecture
------------
    action_map.yaml
          |
          v
    ConfigLoader
          |
          v
    Action Map Validator
          |
          v
    Validated action-map configuration
          |
          v
    Transaction CSV ingestion / transaction validation

Responsibilities
----------------
The validator checks two independent configuration sections:

1. actions:
   Defines transaction-description matching rules and their normalized
   action values.

2. purposes:
   Defines the canonical purpose values and their descriptions.

Validation rules
----------------
Top-level configuration:
    - Must be a mapping.
    - Must contain both 'actions' and 'purposes'.

Actions:
    - Must be a nonempty list.
    - Every entry must be a mapping.
    - Every entry must contain a nonempty string 'match'.
    - Every entry must contain a nonempty string 'normalized'.
    - Match values must be unique, ignoring case and surrounding
      whitespace.

Purposes:
    - Must be a nonempty list.
    - Every entry must be a mapping.
    - Every entry must contain a nonempty string 'value'.
    - Every entry must contain a nonempty string 'description'.
    - Purpose values must be unique, ignoring case and surrounding
      whitespace.

Case-insensitive uniqueness
---------------------------
Configuration values are compared after trimming surrounding whitespace
and applying casefold().

This prevents entries such as 'RMD', 'rmd', and ' Rmd ' from being
treated as distinct purpose values.

The original configuration values are not modified. The validator
checks consistency; normalization behavior belongs to the transaction
ingestion and validation components.

Error handling
--------------
Invalid configuration raises ActionMapValidationError, a ValueError
subclass, with a description of the problem.

Unexpected errors are logged with their traceback and re-raised.
Exceptions are never silently suppressed.

Integration
-----------
ConfigLoader should invoke validate_action_map() immediately after
loading action_map.yaml and before returning the system configuration.

The validator is deliberately independent of YAML file access,
databases, transaction data, market data, and trade execution.

Important
---------
A successful validation confirms that the action-map configuration has
the required structure and unique canonical matching values. It does
not establish that the configured matching rules correctly classify
every possible transaction description.
"""

from collections.abc import Mapping

from core.logger import get_logger

logger = get_logger(__name__)


class ActionMapValidationError(ValueError):
    """Raised when the transaction action-map configuration is invalid."""


def validate_action_map(action_map: object) -> None:
    """
    Validate action normalization rules and transaction purpose definitions.

    The function validates the supplied configuration without modifying it.

    Args:
        action_map: Loaded action-map configuration.

    Raises:
        ActionMapValidationError:
            If the configuration has missing sections, invalid entries,
            missing required fields, empty strings, or duplicate values.
        Exception:
            Unexpected errors are logged and propagated.
    """
    logger.info("Starting action-map configuration validation.")

    try:
        # The root configuration must support named section lookups.
        if not isinstance(action_map, Mapping):
            raise ActionMapValidationError(
                "Action-map configuration must be a mapping."
            )

        # Validate each required section independently so that errors
        # identify whether the problem belongs to actions or purposes.
        for section in ("actions", "purposes"):
            if section not in action_map:
                raise ActionMapValidationError(
                    f"Action-map configuration is missing '{section}'."
                )

            entries: object = action_map[section]

            # An empty section would silently disable the corresponding
            # normalization or purpose-validation behavior.
            if not isinstance(entries, list) or not entries:
                raise ActionMapValidationError(
                    f"Action-map '{section}' must be a nonempty list."
                )

            # Action rules require a matching expression and its
            # normalized result. Purpose definitions require a canonical
            # value and a human-readable description.
            required_fields: tuple[str, str] = (
                ("match", "normalized")
                if section == "actions"
                else ("value", "description")
            )

            # Track canonicalized values to detect duplicates regardless
            # of capitalization or surrounding whitespace.
            seen_values: set[str] = set()

            for index, entry in enumerate(entries):
                # Each list item must be a mapping containing the
                # fields required by its section.
                if not isinstance(entry, Mapping):
                    raise ActionMapValidationError(
                        f"Action-map '{section}' entry {index} "
                        "must be a mapping."
                    )

                # Required fields must be strings containing meaningful
                # content. Whitespace-only values are not valid.
                for field in required_fields:
                    value: object = entry.get(field)

                    if not isinstance(value, str) or not value.strip():
                        raise ActionMapValidationError(
                            f"Action-map '{section}' entry {index} "
                            f"must have a nonempty string '{field}'."
                        )

                # Action matching keys and purpose values must be unique.
                # Normalized action results are intentionally not required
                # to be unique because different descriptions may map to
                # the same normalized transaction action.
                unique_field: str = (
                    "match" if section == "actions" else "value"
                )

                unique_value: str = (
                    str(entry[unique_field]).strip().casefold()
                )

                if unique_value in seen_values:
                    raise ActionMapValidationError(
                        f"Duplicate '{unique_field}' value in "
                        f"action-map '{section}': "
                        f"'{entry[unique_field]}'."
                    )

                seen_values.add(unique_value)

    except ActionMapValidationError:
        # Expected configuration failures are logged and propagated
        # so ConfigLoader can fail immediately.
        logger.warning("Action-map configuration validation failed.")
        raise

    except Exception:
        # Preserve unexpected exceptions and their original tracebacks.
        logger.exception(
            "Unexpected error during action-map configuration validation."
        )
        raise

    logger.info("Action-map configuration validation passed.")

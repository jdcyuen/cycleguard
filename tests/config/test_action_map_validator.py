import pytest

from config.action_map_validator import (
    ActionMapValidationError,
    validate_action_map,
)


@pytest.fixture
def valid_action_map() -> dict[str, list[dict[str, str]]]:
    """Provide a valid action-map configuration for validator tests."""
    return {
        "actions": [
            {
                "match": "LIQUIDATION LIQ PAYOUT",
                "normalized": "DISTRIBUTION",
            },
            {
                "match": "ROTH CONVERSION",
                "normalized": "CONVERSION",
            },
        ],
        "purposes": [
            {
                "value": "RMD",
                "description": "Required Minimum Distribution",
            },
            {
                "value": "ROTH_CONVERSION",
                "description": "Traditional IRA to Roth IRA conversion",
            },
        ],
    }


def test_valid_action_map_passes(
    valid_action_map: dict[str, list[dict[str, str]]],
) -> None:
    """Accept a structurally valid action-map configuration."""
    validate_action_map(valid_action_map)


def test_non_mapping_configuration_is_rejected() -> None:
    """Reject a configuration whose root is not a mapping."""
    with pytest.raises(ActionMapValidationError, match="must be a mapping"):
        validate_action_map([])


@pytest.mark.parametrize("missing_section", ["actions", "purposes"])
def test_missing_section_is_rejected(
    valid_action_map: dict[str, list[dict[str, str]]],
    missing_section: str,
) -> None:
    """Require both action-map sections."""
    action_map: dict[str, list[dict[str, str]]] = valid_action_map.copy()
    del action_map[missing_section]

    with pytest.raises(ActionMapValidationError, match="is missing"):
        validate_action_map(action_map)


@pytest.mark.parametrize("section", ["actions", "purposes"])
def test_empty_section_is_rejected(
    valid_action_map: dict[str, list[dict[str, str]]],
    section: str,
) -> None:
    """Reject empty action and purpose definitions."""
    action_map: dict[str, list[dict[str, str]]] = valid_action_map.copy()
    action_map[section] = []

    with pytest.raises(ActionMapValidationError, match="nonempty list"):
        validate_action_map(action_map)


@pytest.mark.parametrize(
    ("section", "entry"),
    [
        ("actions", "invalid"),
        ("purposes", "invalid"),
    ],
)
def test_non_mapping_entry_is_rejected(
    valid_action_map: dict[str, list[dict[str, str]]],
    section: str,
    entry: str,
) -> None:
    """Require each section entry to be a mapping."""
    action_map: dict[str, list[dict[str, str]]] = valid_action_map.copy()
    action_map[section] = [entry]

    with pytest.raises(ActionMapValidationError, match="must be a mapping"):
        validate_action_map(action_map)


@pytest.mark.parametrize(
    ("section", "entry"),
    [
        ("actions", {"normalized": "DISTRIBUTION"}),
        ("actions", {"match": "PAYMENT"}),
        ("purposes", {"description": "Required Minimum Distribution"}),
        ("purposes", {"value": "RMD"}),
    ],
)
def test_missing_required_field_is_rejected(
    valid_action_map: dict[str, list[dict[str, str]]],
    section: str,
    entry: dict[str, str],
) -> None:
    """Require all fields for action rules and purpose definitions."""
    action_map: dict[str, list[dict[str, str]]] = valid_action_map.copy()
    action_map[section] = [entry]

    with pytest.raises(ActionMapValidationError, match="nonempty string"):
        validate_action_map(action_map)


@pytest.mark.parametrize(
    ("section", "entry"),
    [
        ("actions", {"match": " ", "normalized": "DISTRIBUTION"}),
        ("actions", {"match": "PAYMENT", "normalized": ""}),
        ("purposes", {"value": " ", "description": "Description"}),
        ("purposes", {"value": "RMD", "description": ""}),
    ],
)
def test_empty_required_field_is_rejected(
    valid_action_map: dict[str, list[dict[str, str]]],
    section: str,
    entry: dict[str, str],
) -> None:
    """Reject empty and whitespace-only required values."""
    action_map: dict[str, list[dict[str, str]]] = valid_action_map.copy()
    action_map[section] = [entry]

    with pytest.raises(ActionMapValidationError, match="nonempty string"):
        validate_action_map(action_map)


@pytest.mark.parametrize(
    ("section", "duplicate_entry"),
    [
        (
            "actions",
            {"match": " liquidation liq payout ", "normalized": "OTHER"},
        ),
        (
            "purposes",
            {"value": "rmd", "description": "Duplicate purpose"},
        ),
    ],
)
def test_case_insensitive_duplicates_are_rejected(
    valid_action_map: dict[str, list[dict[str, str]]],
    section: str,
    duplicate_entry: dict[str, str],
) -> None:
    """Reject duplicate matching keys and purpose values regardless of case."""
    action_map: dict[str, list[dict[str, str]]] = valid_action_map.copy()
    action_map[section] = (
        action_map[section] + [duplicate_entry]
    )

    with pytest.raises(ActionMapValidationError, match="Duplicate"):
        validate_action_map(action_map)


def test_duplicate_normalized_actions_are_allowed(
    valid_action_map: dict[str, list[dict[str, str]]],
) -> None:
    """Allow different matching rules to produce the same normalized action."""
    valid_action_map["actions"].append(
        {
            "match": "ANOTHER DISTRIBUTION DESCRIPTION",
            "normalized": "DISTRIBUTION",
        }
    )

    validate_action_map(valid_action_map)


def test_validation_does_not_modify_configuration(
    valid_action_map: dict[str, list[dict[str, str]]],
) -> None:
    """Preserve original configuration values during validation."""
    original: dict[str, list[dict[str, str]]] = {
        section: [entry.copy() for entry in entries]
        for section, entries in valid_action_map.items()
    }

    validate_action_map(valid_action_map)

    assert valid_action_map == original
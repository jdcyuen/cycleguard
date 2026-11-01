
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from cli.drift_detection_cli import display_accounts, select_account


@pytest.fixture
def account_matches():
    """Provide database accounts paired with their YAML configurations."""
    rollover_db = SimpleNamespace(name="ROLLOVER")
    rollover_config = SimpleNamespace(name="Rollover IRA")

    roth_db = SimpleNamespace(name="ROTH")
    roth_config = SimpleNamespace(name="Roth IRA")

    return [
        (rollover_db, rollover_config),
        (roth_db, roth_config),
    ]


def test_display_accounts_prints_database_and_config_names(
    account_matches,
    capsys,
):
    display_accounts(account_matches)

    output = capsys.readouterr().out

    assert "1. Rollover IRA (database: ROLLOVER)" in output
    assert "2. Roth IRA (database: ROTH)" in output


def test_select_account_matches_yaml_name_case_insensitively(
    account_matches,
):
    selected = select_account(account_matches, "  ROLLOVER IRA  ")

    assert selected == account_matches[0]


def test_select_account_matches_database_name(account_matches):
    selected = select_account(account_matches, "ROTH")

    assert selected == account_matches[1]


def test_select_account_rejects_empty_matches():
    with pytest.raises(ValueError, match="No database accounts match"):
        select_account([])


def test_select_account_rejects_unknown_name(account_matches):
    with pytest.raises(ValueError, match="was not found") as exc_info:
        select_account(account_matches, "Traditional IRA")

    assert "Rollover IRA" in str(exc_info.value)
    assert "Roth IRA" in str(exc_info.value)


def test_select_account_rejects_ambiguous_name():
    matches = [
        (
            SimpleNamespace(name="IRA"),
            SimpleNamespace(name="Rollover IRA"),
        ),
        (
            SimpleNamespace(name="ROTH"),
            SimpleNamespace(name="IRA"),
        ),
    ]

    with pytest.raises(ValueError, match="is ambiguous"):
        select_account(matches, "IRA")


def test_select_account_prompts_for_valid_number(
    account_matches,
):
    with patch(
        "cli.drift_detection_cli.input",
        side_effect=["2"],
    ):
        selected = select_account(account_matches)

    assert selected == account_matches[1]


def test_select_account_retries_after_invalid_input(
    account_matches,
    capsys,
):
    with patch(
        "cli.drift_detection_cli.input",
        side_effect=["invalid", "9", "1"],
    ):
        selected = select_account(account_matches)

    output = capsys.readouterr().out

    assert selected == account_matches[0]
    assert "Enter the number beside the account." in output
    assert "Enter a number from 1 to 2." in output

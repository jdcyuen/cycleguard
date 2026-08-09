from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import config.config_manager as config_manager


# ============================================================
# BASE_DIR TEST
# ============================================================

def test_base_dir_exists():
    assert isinstance(config_manager.BASE_DIR, Path)


# ============================================================
# _resolve_config_path TESTS
# ============================================================

def test_resolve_test_config_path():
    path = config_manager._resolve_config_path("test")

    assert Path(path).as_posix().endswith(
        "tests/config/test.yaml"
    )


def test_resolve_prod_config_path():
    path = config_manager._resolve_config_path("prod")

    assert Path(path).as_posix().endswith(
        "src/config/prod.yaml"
    )


def test_resolve_default_dev_config_path():
    path = config_manager._resolve_config_path("dev")

    assert Path(path).as_posix().endswith(
        "src/config/dev.yaml"
    )


def test_resolve_unknown_environment_defaults_to_dev():
    path = config_manager._resolve_config_path(
        "unknown"
    )

    assert Path(path).as_posix().endswith(
        "src/config/dev.yaml"
    )


# ============================================================
# load_dotenv TESTS
# ============================================================

def test_load_dotenv_loads_values(tmp_path, monkeypatch):
    dotenv = tmp_path / ".env"

    dotenv.write_text(
        """
        TEST_KEY=value123
        QUOTED_KEY="hello"
        SINGLE_KEY='world'
        # COMMENT=value
        """,
        encoding="utf-8",
    )

    monkeypatch.setattr(
        config_manager,
        "BASE_DIR",
        tmp_path,
    )

    monkeypatch.delenv(
        "TEST_KEY",
        raising=False,
    )

    monkeypatch.delenv(
        "QUOTED_KEY",
        raising=False,
    )

    monkeypatch.delenv(
        "SINGLE_KEY",
        raising=False,
    )

    config_manager.load_dotenv()

    assert (
        config_manager.os.environ["TEST_KEY"]
        == "value123"
    )

    assert (
        config_manager.os.environ["QUOTED_KEY"]
        == "hello"
    )

    assert (
        config_manager.os.environ["SINGLE_KEY"]
        == "world"
    )


def test_load_dotenv_does_not_override_existing_env(
    tmp_path,
    monkeypatch,
):
    dotenv = tmp_path / ".env"

    dotenv.write_text(
        "EXISTING=value_from_file",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        config_manager,
        "BASE_DIR",
        tmp_path,
    )

    monkeypatch.setenv(
        "EXISTING",
        "existing_value",
    )

    config_manager.load_dotenv()

    assert (
        config_manager.os.environ["EXISTING"]
        == "existing_value"
    )


def test_load_dotenv_missing_file(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        config_manager,
        "BASE_DIR",
        tmp_path,
    )

    # should not raise exception
    config_manager.load_dotenv()


# ============================================================
# get_config TESTS
# ============================================================

@pytest.fixture(autouse=True)
def clear_config_cache():
    """
    Prevent tests affecting each other.
    """
    config_manager.get_config.cache_clear()

    yield

    config_manager.get_config.cache_clear()


def test_get_config_calls_loader():
    fake_config = {
        "environment": "test"
    }

    with patch(
        "config.config_manager.ConfigLoader"
    ) as mock_loader:

        instance = mock_loader.return_value

        instance.load.return_value = fake_config

        result = config_manager.get_config(
            "test"
        )

    mock_loader.assert_called_once()

    instance.load.assert_called_once()

    assert result == fake_config


def test_get_config_uses_environment_variable(
    monkeypatch,
):
    fake_config = {
        "environment": "dev"
    }

    monkeypatch.setenv(
        "CYCLEGUARD_ENV",
        "dev",
    )

    with patch(
        "config.config_manager.ConfigLoader"
    ) as mock_loader:

        mock_loader.return_value.load.return_value = (
            fake_config
        )

        result = config_manager.get_config()

    assert result == fake_config


def test_get_config_defaults_to_dev_when_no_env(
    monkeypatch,
):
    monkeypatch.delenv(
        "CYCLEGUARD_ENV",
        raising=False,
    )

    with patch(
        "config.config_manager.ConfigLoader"
    ) as mock_loader:

        mock_loader.return_value.load.return_value = {}

        config_manager.get_config()

    called_path = (
        mock_loader.call_args.args[0]
    )

    assert Path(called_path).as_posix().endswith(
        "src/config/dev.yaml"
    )


# ============================================================
# CACHE TESTS
# ============================================================

def test_get_config_is_cached():

    with patch(
        "config.config_manager.ConfigLoader"
    ) as mock_loader:

        mock_loader.return_value.load.return_value = {
            "x": 1
        }

        first = config_manager.get_config(
            "test"
        )

        second = config_manager.get_config(
            "test"
        )

    assert first is second

    mock_loader.assert_called_once()


def test_clear_config_cache():

    with patch(
        "config.config_manager.ConfigLoader"
    ) as mock_loader:

        mock_loader.return_value.load.return_value = {
            "x": 1
        }

        config_manager.get_config("test")

        config_manager.clear_config_cache()

        config_manager.get_config("test")

    assert (
        mock_loader.call_count
        == 2
    )


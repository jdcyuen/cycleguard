import pytest
from datetime import date

from data.providers.cape_data_provider import CapeDataProvider
from data.providers.data_provider_error import DataProviderError

def test_get_latest_returns_latest_cape():
    provider = CapeDataProvider()

    result = provider.get_latest()

    assert result["date"] == "2026.09"
    assert result["cape"] == pytest.approx(40.575838)


def test_get_for_date_returns_latest_observation_on_or_before_date():
    provider = CapeDataProvider()

    result = provider.get_for_date(date(2026, 8, 15))

    assert result["date"] == "2026.08"
    assert result["cape"] == pytest.approx(41.119844)

def test_get_latest_raises_data_provider_error_when_file_is_missing(tmp_path):
    provider = CapeDataProvider(
        data_file=str(tmp_path / "missing.xls")
    )

    with pytest.raises(DataProviderError):
        provider.get_latest()
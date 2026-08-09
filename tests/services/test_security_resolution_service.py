# tests/services/test_security_resolution_service.py

from unittest.mock import MagicMock, patch

from models.security import Security
from services.security_resolution_service import (
    SecurityResolutionService,
)


#
# Fixtures
#

def make_service():
    repo = MagicMock()
    service = SecurityResolutionService(repo)
    return service, repo


#
# get_missing_fields()
#

def test_get_missing_fields_returns_missing_fields():

    security = Security(
        symbol="AAPL",
        description=None,
        asset_type="EQUITY",
    )

    missing = SecurityResolutionService.get_missing_fields(
        security
    )

    assert "description" in missing
    assert "symbol" not in missing
    assert "asset_type" not in missing


#
# get_quote_type()
#

@patch("services.security_resolution_service.yf.Ticker")
def test_get_quote_type_returns_quote_type(mock_ticker):

    mock_ticker.return_value.info = {
        "quoteType": "EQUITY"
    }

    service, _ = make_service()

    result = service.get_quote_type("AAPL")

    assert result == "EQUITY"


@patch("services.security_resolution_service.yf.Ticker")
def test_get_quote_type_returns_none_on_exception(mock_ticker):

    mock_ticker.side_effect = Exception("Yahoo failure")

    service, _ = make_service()

    result = service.get_quote_type("AAPL")

    assert result is None


#
# resolve()
#

@patch.object(
    SecurityResolutionService,
    "get_quote_type",
)
def test_resolve_sets_asset_type_and_upserts(
    mock_quote_type,
):

    mock_quote_type.return_value = "ETF"

    service, repo = make_service()

    security = Security(
        symbol="VOO",
        description="Vanguard S&P 500 ETF",
    )

    repo.upsert.return_value = security

    result = service.resolve(security)

    assert security.asset_type == "ETF"

    repo.upsert.assert_called_once_with(security)

    assert result == security


@patch.object(
    SecurityResolutionService,
    "get_quote_type",
)
def test_resolve_normalizes_fdrxx(
    mock_quote_type,
):

    mock_quote_type.return_value = "MUTUALFUND"

    service, repo = make_service()

    repo.upsert.side_effect = lambda x: x

    security = Security(
        symbol="FDRXX",
    )

    result = service.resolve(security)

    assert result.symbol == "FDRXX"

    assert (
        result.description
        == "Fidelity Government Cash Reserves"
    )

    assert result.asset_type == "MUTUALFUND"

    repo.upsert.assert_called_once()
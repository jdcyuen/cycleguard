from unittest.mock import MagicMock

from services.portfolio_aggregation_service import (
    PortfolioAggregationService,
)

from models.portfolio_bucket import PortfolioBucket
from decimal import Decimal
import pytest

def test_get_positions():
    position_repository = MagicMock()
    account = MagicMock()

    expected_positions = [
        MagicMock(),
        MagicMock(),
    ]

    position_repository.get_by_snapshot_with_security.return_value = (
        expected_positions
    )

    service = PortfolioAggregationService(
        position_repository,
        account,
    )

    result = service.get_positions(123)

    assert result == expected_positions

    position_repository.get_by_snapshot_with_security.assert_called_once_with(
        123
    )


def test_get_bucket_mapping():
    position_repository = MagicMock()
    account = MagicMock()

    account.bucket_mapping = {
        "FZROX": "core_equity",
        "SCHD": "equity_income",
    }

    service = PortfolioAggregationService(
        position_repository,
        account,
    )

    result = service.get_bucket_mapping()

    assert result == {
        "FZROX": "core_equity",
        "SCHD": "equity_income",
    }

def test_map_positions_to_buckets():
    position_repository = MagicMock()
    account = MagicMock()

    position_fzrox = MagicMock()
    position_fzrox.symbol = "FZROX"

    position_schd = MagicMock()
    position_schd.symbol = "SCHD"

    position_repository.get_by_snapshot_with_security.return_value = [
        position_fzrox,
        position_schd,
    ]

    account.bucket_mapping = {
        "FZROX": "core_equity",
        "SCHD": "equity_income",
    }

    service = PortfolioAggregationService(
        position_repository,
        account,
    )

    result = service.map_positions_to_buckets(123)

    assert result == {
        "core_equity": [position_fzrox],
        "equity_income": [position_schd],
    }


def test_map_positions_to_buckets_raises_for_unmapped_symbol():
    position_repository = MagicMock()
    account = MagicMock()

    position = MagicMock()
    position.symbol = "UNKNOWN"

    position_repository.get_by_snapshot_with_security.return_value = [
        position,
    ]

    account.bucket_mapping = {}

    service = PortfolioAggregationService(
        position_repository,
        account,
    )

    with pytest.raises(
        ValueError,
        match="No bucket mapping found for symbol UNKNOWN",
    ):
        service.map_positions_to_buckets(123)

def test_calculate_bucket_values():
    position_repository = MagicMock()
    account = MagicMock()

    position_fzrox = MagicMock()
    position_fzrox.symbol = "FZROX"
    position_fzrox.current_value = 100000

    position_schd = MagicMock()
    position_schd.symbol = "SCHD"
    position_schd.current_value = 50000

    position_sgov = MagicMock()
    position_sgov.symbol = "SGOV"
    position_sgov.current_value = 25000

    position_repository.get_by_snapshot_with_security.return_value = [
        position_fzrox,
        position_schd,
        position_sgov,
    ]

    account.bucket_mapping = {
        "FZROX": "core_equity",
        "SCHD": "equity_income",
        "SGOV": "defensive",
    }

    service = PortfolioAggregationService(
        position_repository,
        account,
    )

    result = service.calculate_bucket_values(123)

    assert result == {
        "core_equity": 100000,
        "equity_income": 50000,
        "defensive": 25000,
    }

def test_calculate_portfolio_value():
    position_repository = MagicMock()
    account = MagicMock()

    position_fzrox = MagicMock()
    position_fzrox.symbol = "FZROX"
    position_fzrox.current_value = 100000

    position_schd = MagicMock()
    position_schd.symbol = "SCHD"
    position_schd.current_value = 50000

    position_sgov = MagicMock()
    position_sgov.symbol = "SGOV"
    position_sgov.current_value = 25000

    position_repository.get_by_snapshot_with_security.return_value = [
        position_fzrox,
        position_schd,
        position_sgov,
    ]

    service = PortfolioAggregationService(
        position_repository,
        account,
    )

    result = service.calculate_portfolio_value(123)

    assert result == 175000

def test_calculate_bucket_weights():
    position_repository = MagicMock()
    account = MagicMock()

    position_fzrox = MagicMock()
    position_fzrox.symbol = "FZROX"
    position_fzrox.current_value = Decimal("100000")

    position_schd = MagicMock()
    position_schd.symbol = "SCHD"
    position_schd.current_value = Decimal("50000")

    position_sgov = MagicMock()
    position_sgov.symbol = "SGOV"
    position_sgov.current_value = Decimal("25000")

    position_repository.get_by_snapshot_with_security.return_value = [
        position_fzrox,
        position_schd,
        position_sgov,
    ]

    account.bucket_mapping = {
        "FZROX": "core_equity",
        "SCHD": "equity_income",
        "SGOV": "defensive",
    }

    service = PortfolioAggregationService(
        position_repository,
        account,
    )

    result = service.calculate_bucket_weights(123)

    assert result["core_equity"] == Decimal("100000") / Decimal("175000")
    assert result["equity_income"] == Decimal("50000") / Decimal("175000")
    assert result["defensive"] == Decimal("25000") / Decimal("175000")

def test_calculate_bucket_weights_zero_portfolio_value():
    position_repository = MagicMock()
    account = MagicMock()

    position = MagicMock()
    position.symbol = "FZROX"
    position.current_value = Decimal("0")

    position_repository.get_by_snapshot_with_security.return_value = [
        position,
    ]

    account.bucket_mapping = {
        "FZROX": "core_equity",
    }

    service = PortfolioAggregationService(
        position_repository,
        account,
    )

    result = service.calculate_bucket_weights(123)

    assert result == {
        "core_equity": Decimal("0"),
    }

def test_get_target_weights():
    position_repository = MagicMock()
    account = MagicMock()

    account.bucket_weights = {
        "defensive": Decimal("0.15"),
        "fixed_income": Decimal("0.30"),
        "core_equity": Decimal("0.20"),
        "equity_income": Decimal("0.20"),
        "equity_growth": Decimal("0.15"),
    }

    service = PortfolioAggregationService(
        position_repository,
        account,
    )

    result = service.get_target_weights()

    assert result == account.bucket_weights


def test_get_bucket_allocation():
    position_repository = MagicMock()
    account = MagicMock()

    position_fzrox = MagicMock()
    position_fzrox.symbol = "FZROX"
    position_fzrox.current_value = Decimal("100000")

    position_schd = MagicMock()
    position_schd.symbol = "SCHD"
    position_schd.current_value = Decimal("50000")

    position_repository.get_by_snapshot_with_security.return_value = [
        position_fzrox,
        position_schd,
    ]

    account.bucket_mapping = {
        "FZROX": "core_equity",
        "SCHD": "equity_income",
    }

    account.bucket_weights = {
        "core_equity": Decimal("0.60"),
        "equity_income": Decimal("0.40"),
    }

    service = PortfolioAggregationService(
        position_repository,
        account,
    )

    result = service.get_bucket_allocation(123)

    assert result["core_equity"].actual_weight == (
        Decimal("100000") / Decimal("150000")
    )

    assert result["core_equity"].target_weight == Decimal("0.60")

    assert result["equity_income"].actual_weight == (
        Decimal("50000") / Decimal("150000")
    )

    assert result["equity_income"].target_weight == Decimal("0.40")

def test_get_bucket_allocation_includes_drift():
    position_repository = MagicMock()
    account = MagicMock()

    position_fzrox = MagicMock()
    position_fzrox.symbol = "FZROX"
    position_fzrox.current_value = Decimal("100000")

    position_schd = MagicMock()
    position_schd.symbol = "SCHD"
    position_schd.current_value = Decimal("50000")

    position_repository.get_by_snapshot_with_security.return_value = [
        position_fzrox,
        position_schd,
    ]

    account.bucket_mapping = {
        "FZROX": "core_equity",
        "SCHD": "equity_income",
    }

    account.bucket_weights = {
        "core_equity": Decimal("0.60"),
        "equity_income": Decimal("0.40"),
    }

    service = PortfolioAggregationService(
        position_repository,
        account,
    )

    result = service.get_bucket_allocation(123)

    assert result["core_equity"].drift == (
        Decimal("100000") / Decimal("150000")
        - Decimal("0.60")
    )

    assert result["equity_income"].drift == (
        Decimal("50000") / Decimal("150000")
        - Decimal("0.40")
    )

    assert result["core_equity"].drift_value == Decimal("10000")
    assert result["equity_income"].drift_value == Decimal("-10000")

    assert result["core_equity"].name == "core_equity"
    assert result["core_equity"].market_value == Decimal("100000")

    assert result["equity_income"].name == "equity_income"
    assert result["equity_income"].market_value == Decimal("50000")

def test_get_bucket_allocation_retrieves_positions_once():
    position_repository = MagicMock()
    account = MagicMock()

    position_fzrox = MagicMock()
    position_fzrox.symbol = "FZROX"
    position_fzrox.current_value = Decimal("100000")

    position_schd = MagicMock()
    position_schd.symbol = "SCHD"
    position_schd.current_value = Decimal("50000")

    position_repository.get_by_snapshot_with_security.return_value = [
        position_fzrox,
        position_schd,
    ]

    account.bucket_mapping = {
        "FZROX": "core_equity",
        "SCHD": "equity_income",
    }

    account.bucket_weights = {
        "core_equity": Decimal("0.60"),
        "equity_income": Decimal("0.40"),
    }

    service = PortfolioAggregationService(
        position_repository,
        account,
    )

    service.get_bucket_allocation(123)

    assert (
        position_repository.get_by_snapshot_with_security.call_count
        == 1
    )

def test_get_bucket_allocation_with_zero_portfolio_value():
    position_repository = MagicMock()
    account = MagicMock()

    position_repository.get_by_snapshot_with_security.return_value = []

    account.bucket_mapping = {}
    account.bucket_weights = {
        "core_equity": Decimal("0.60"),
        "equity_income": Decimal("0.40"),
    }

    service = PortfolioAggregationService(
        position_repository,
        account,
    )

    result = service.get_bucket_allocation(123)

    assert result["core_equity"].market_value == Decimal("0")
    assert result["core_equity"].actual_weight == Decimal("0")
    assert result["core_equity"].target_weight == Decimal("0.60")
    assert result["core_equity"].drift == Decimal("-0.60")
    assert result["core_equity"].drift_value == Decimal("0")

    assert result["equity_income"].market_value == Decimal("0")
    assert result["equity_income"].actual_weight == Decimal("0")
    assert result["equity_income"].target_weight == Decimal("0.40")
    assert result["equity_income"].drift == Decimal("-0.40")
    assert result["equity_income"].drift_value == Decimal("0")

def test_get_bucket_allocation_raises_for_unmapped_symbol():
    position_repository = MagicMock()
    account = MagicMock()

    position = MagicMock()
    position.symbol = "UNKNOWN"
    position.current_value = Decimal("10000")

    position_repository.get_by_snapshot_with_security.return_value = [
        position
    ]

    account.bucket_mapping = {}
    account.bucket_weights = {}

    service = PortfolioAggregationService(
        position_repository,
        account,
    )

    with pytest.raises(
        ValueError,
        match="No bucket mapping found for symbol UNKNOWN",
    ):
        service.get_bucket_allocation(123)
    
def test_get_bucket_allocation_includes_target_bucket_with_no_positions():
    position_repository = MagicMock()
    account = MagicMock()

    position_fzrox = MagicMock()
    position_fzrox.symbol = "FZROX"
    position_fzrox.current_value = Decimal("100000")

    position_repository.get_by_snapshot_with_security.return_value = [
        position_fzrox,
    ]

    account.bucket_mapping = {
        "FZROX": "core_equity",
    }

    account.bucket_weights = {
        "core_equity": Decimal("0.60"),
        "equity_income": Decimal("0.40"),
    }

    service = PortfolioAggregationService(
        position_repository,
        account,
    )

    result = service.get_bucket_allocation(123)

    assert "equity_income" in result

    assert result["equity_income"].market_value == Decimal("0")
    assert result["equity_income"].actual_weight == Decimal("0")
    assert result["equity_income"].target_weight == Decimal("0.40")
    assert result["equity_income"].drift == Decimal("-0.40")
    assert result["equity_income"].drift_value == Decimal("-40000")

def test_get_bucket_allocation_includes_bucket_without_target_weight():
    position_repository = MagicMock()
    account = MagicMock()

    position_fzrox = MagicMock()
    position_fzrox.symbol = "FZROX"
    position_fzrox.current_value = Decimal("100000")

    position_repository.get_by_snapshot_with_security.return_value = [
        position_fzrox,
    ]

    account.bucket_mapping = {
        "FZROX": "core_equity",
    }

    account.bucket_weights = {}

    service = PortfolioAggregationService(
        position_repository,
        account,
    )

    result = service.get_bucket_allocation(123)

    assert "core_equity" in result
    assert result["core_equity"].market_value == Decimal("100000")
    assert result["core_equity"].actual_weight == Decimal("1")
    assert result["core_equity"].target_weight == Decimal("0")
    assert result["core_equity"].drift == Decimal("1")
    assert result["core_equity"].drift_value == Decimal("100000")

def test_get_bucket_allocation_uses_snapshot_id():
    position_repository = MagicMock()
    account = MagicMock()

    position_repository.get_by_snapshot_with_security.return_value = []

    account.bucket_mapping = {}
    account.bucket_weights = {}

    service = PortfolioAggregationService(
        position_repository,
        account,
    )

    service.get_bucket_allocation(456)

    position_repository.get_by_snapshot_with_security.assert_called_once_with(
        456
    )

def test_get_portfolio_value():
    position_repository = MagicMock()
    account = MagicMock()

    position_fzrox = MagicMock()
    position_fzrox.current_value = Decimal("100000")

    position_schd = MagicMock()
    position_schd.current_value = Decimal("50000")

    position_repository.get_by_snapshot_with_security.return_value = [
        position_fzrox,
        position_schd,
    ]

    service = PortfolioAggregationService(
        position_repository,
        account,
    )

    result = service.get_portfolio_value(123)

    assert result == Decimal("150000")

def test_map_positions_to_buckets_groups_positions():
    position_repository = MagicMock()
    account = MagicMock()

    position_fzrox = MagicMock()
    position_fzrox.symbol = "FZROX"

    position_schd = MagicMock()
    position_schd.symbol = "SCHD"

    position_repository.get_by_snapshot_with_security.return_value = [
        position_fzrox,
        position_schd,
    ]

    account.bucket_mapping = {
        "FZROX": "core_equity",
        "SCHD": "equity_income",
    }

    service = PortfolioAggregationService(
        position_repository,
        account,
    )

    result = service.map_positions_to_buckets(123)

    assert result["core_equity"] == [position_fzrox]
    assert result["equity_income"] == [position_schd]

def test_calculate_position_bucket_weights():
    position_repository = MagicMock()
    account = MagicMock()

    position_fzrox = MagicMock()
    position_fzrox.symbol = "FZROX"
    position_fzrox.current_value = Decimal("100000")

    position_schd = MagicMock()
    position_schd.symbol = "SCHD"
    position_schd.current_value = Decimal("50000")

    position_repository.get_by_snapshot_with_security.return_value = [
        position_fzrox,
        position_schd,
    ]

    account.bucket_mapping = {
        "FZROX": "core_equity",
        "SCHD": "equity_income",
    }

    service = PortfolioAggregationService(
        position_repository,
        account,
    )

    result = service.calculate_position_bucket_weights(123)

    assert result["core_equity"][0].symbol == "FZROX"
    assert result["core_equity"][0].weight == Decimal("1")

    assert result["equity_income"][0].symbol == "SCHD"
    assert result["equity_income"][0].weight == Decimal("1")


def test_calculate_position_bucket_weights_with_multiple_positions():
    position_repository = MagicMock()
    account = MagicMock()

    position_fzrox = MagicMock()
    position_fzrox.symbol = "FZROX"
    position_fzrox.current_value = Decimal("100000")

    position_vti = MagicMock()
    position_vti.symbol = "VTI"
    position_vti.current_value = Decimal("50000")

    position_schd = MagicMock()
    position_schd.symbol = "SCHD"
    position_schd.current_value = Decimal("50000")

    position_repository.get_by_snapshot_with_security.return_value = [
        position_fzrox,
        position_vti,
        position_schd,
    ]

    account.bucket_mapping = {
        "FZROX": "core_equity",
        "VTI": "core_equity",
        "SCHD": "equity_income",
    }

    service = PortfolioAggregationService(
        position_repository,
        account,
    )

    result = service.calculate_position_bucket_weights(123)

    assert result["core_equity"][0].symbol == "FZROX"
    assert result["core_equity"][0].weight == Decimal(
        "0.6666666666666666666666666667"
    )

    assert result["core_equity"][1].symbol == "VTI"
    assert result["core_equity"][1].weight == Decimal(
        "0.3333333333333333333333333333"
    )

    assert result["equity_income"][0].symbol == "SCHD"
    assert result["equity_income"][0].weight == Decimal("1")

    assert result["core_equity"][0].bucket == "core_equity"
    assert result["core_equity"][0].market_value == Decimal("100000")

    assert result["core_equity"][1].bucket == "core_equity"
    assert result["core_equity"][1].market_value == Decimal("50000")

    assert result["equity_income"][0].bucket == "equity_income"
    assert result["equity_income"][0].market_value == Decimal("50000")
    

def test_calculate_position_bucket_weights_with_zero_bucket_value():
    position_repository = MagicMock()
    account = MagicMock()

    position_fzrox = MagicMock()
    position_fzrox.symbol = "FZROX"
    position_fzrox.current_value = Decimal("0")

    position_repository.get_by_snapshot_with_security.return_value = [
        position_fzrox,
    ]

    account.bucket_mapping = {
        "FZROX": "core_equity",
    }

    service = PortfolioAggregationService(
        position_repository,
        account,
    )

    result = service.calculate_position_bucket_weights(123)

    assert result["core_equity"][0].symbol == "FZROX"
    assert result["core_equity"][0].weight == Decimal("0")


def test_get_portfolio_allocation():
    position_repository = MagicMock()
    account = MagicMock()

    position_fzrox = MagicMock()
    position_fzrox.symbol = "FZROX"
    position_fzrox.current_value = Decimal("100000")

    position_schd = MagicMock()
    position_schd.symbol = "SCHD"
    position_schd.current_value = Decimal("50000")

    position_repository.get_by_snapshot_with_security.return_value = [
        position_fzrox,
        position_schd,
    ]

    account.bucket_mapping = {
        "FZROX": "core_equity",
        "SCHD": "equity_income",
    }

    account.bucket_weights = {
        "core_equity": Decimal("0.60"),
        "equity_income": Decimal("0.40"),
    }

    service = PortfolioAggregationService(
        position_repository,
        account,
    )

    result = service.get_portfolio_allocation(123)

    assert result.portfolio_value == Decimal("150000")
    assert result.buckets["core_equity"].market_value == Decimal("100000")
    assert result.buckets["equity_income"].market_value == Decimal("50000")
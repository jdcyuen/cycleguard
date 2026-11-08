
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from models.position import Position
from models.portfolio_view import (
    PortfolioAccountView,
    PortfolioHolding,
)
from services.portfolio_view_orchestration_service import (
    PortfolioViewOrchestrationService,
)


@pytest.fixture
def service():
    """Create the orchestration service without external dependencies."""
    return PortfolioViewOrchestrationService.__new__(
        PortfolioViewOrchestrationService
    )


@pytest.fixture
def account_view():
    """Create an account view with lightweight account/config mocks."""
    return PortfolioAccountView(
        database_account=MagicMock(),
        account_config=MagicMock(name="Test Account"),
    )


def make_holding(
    symbol: str,
    percentage: Decimal | None,
    bucket: str = "core_equity",
    current_value: Decimal = Decimal("1000"),
) -> PortfolioHolding:
    """Create a holding backed by a real immutable Position."""
    position = Position(
        symbol=symbol,
        current_value=current_value,
        percent_of_account=percentage,
    )

    return PortfolioHolding(
        position=position,
        bucket=bucket,
        account_name="Test Account",
    )


class TestPositionPercentageValidation:
    """Tests for snapshot position percentage reconciliation."""

    def test_exactly_100_percent_has_no_warning(
        self, service, account_view
    ):
        holdings = [
            make_holding("AAA", Decimal("60")),
            make_holding("BBB", Decimal("40")),
        ]

        service._validate_position_percentages(
            holdings, account_view
        )

        assert account_view.validation_warnings == []

    def test_within_tolerance_has_no_warning(
        self, service, account_view
    ):
        holdings = [
            make_holding("AAA", Decimal("60.02")),
            make_holding("BBB", Decimal("40")),
        ]

        service._validate_position_percentages(
            holdings, account_view
        )

        assert account_view.validation_warnings == []

    def test_outside_tolerance_generates_warning(
        self, service, account_view
    ):
        holdings = [
            make_holding("AAA", Decimal("60.06")),
            make_holding("BBB", Decimal("40")),
        ]

        service._validate_position_percentages(
            holdings, account_view
        )

        assert len(account_view.validation_warnings) == 1
        assert "do not reconcile to 100%" in (
            account_view.validation_warnings[0]
        )
        assert "100.0600%" in account_view.validation_warnings[0]

    def test_missing_percentage_generates_incomplete_warning(
        self, service, account_view
    ):
        holdings = [
            make_holding("AAA", Decimal("60")),
            make_holding("BBB", None),
        ]

        service._validate_position_percentages(
            holdings, account_view
        )

        assert len(account_view.validation_warnings) == 1
        assert "incomplete" in account_view.validation_warnings[0]
        assert "BBB" in account_view.validation_warnings[0]
        assert "do not reconcile" not in (
            account_view.validation_warnings[0]
        )

    def test_empty_holdings_generates_incomplete_warning(
        self, service, account_view
    ):
        service._validate_position_percentages(
            [], account_view
        )

        assert len(account_view.validation_warnings) == 1
        assert "No positions are available" in (
            account_view.validation_warnings[0]
        )
        assert "do not reconcile" not in (
            account_view.validation_warnings[0]
        )

    def test_invalid_holdings_argument_raises_value_error(
        self, service, account_view
    ):
        with pytest.raises(ValueError, match="holdings must be a list"):
            service._validate_position_percentages(
                None, account_view
            )

    def test_missing_account_view_raises_value_error(
        self, service
    ):
        with pytest.raises(ValueError, match="account_view is required"):
            service._validate_position_percentages([], None)


class TestActualAllocationCalculation:
    """Tests for actual bucket allocation calculations."""

    def test_calculates_bucket_market_values_and_percentages(
        self, service
    ):
        holdings = [
            make_holding(
                "AAA", Decimal("30"), "core_equity",
                Decimal("3000"),
            ),
            make_holding(
                "BBB", Decimal("20"), "core_equity",
                Decimal("2000"),
            ),
            make_holding(
                "CCC", Decimal("50"), "fixed_income",
                Decimal("5000"),
            ),
        ]

        allocations = service._calculate_actual_allocations(
            holdings=holdings,
            bucket_names=["core_equity", "fixed_income"],
        )

        assert len(allocations) == 2

        core = allocations[0]
        assert core.bucket == "core_equity"
        assert core.percentage == Decimal("50")
        assert core.market_value == Decimal("5000")
        assert len(core.holdings) == 2

        fixed_income = allocations[1]
        assert fixed_income.bucket == "fixed_income"
        assert fixed_income.percentage == Decimal("50")
        assert fixed_income.market_value == Decimal("5000")
        assert len(fixed_income.holdings) == 1

    def test_includes_empty_configured_buckets(self, service):
        allocations = service._calculate_actual_allocations(
            holdings=[
                make_holding(
                    "AAA", Decimal("100"), "core_equity"
                )
            ],
            bucket_names=["core_equity", "fixed_income"],
        )

        assert len(allocations) == 2
        assert allocations[1].bucket == "fixed_income"
        assert allocations[1].percentage == Decimal("0")
        assert allocations[1].market_value == Decimal("0")
        assert allocations[1].holdings == []

    def test_includes_unmapped_positions(self, service):
        holdings = [
            make_holding(
                "AAA", Decimal("90"), "core_equity",
                Decimal("9000"),
            ),
            make_holding(
                "UNKNOWN", Decimal("10"), "UNMAPPED",
                Decimal("1000"),
            ),
        ]

        allocations = service._calculate_actual_allocations(
            holdings=holdings,
            bucket_names=["core_equity"],
        )

        assert len(allocations) == 2

        unmapped = allocations[1]
        assert unmapped.bucket == "UNMAPPED"
        assert unmapped.percentage == Decimal("10")
        assert unmapped.market_value == Decimal("1000")
        assert len(unmapped.holdings) == 1
        assert unmapped.holdings[0].position.symbol == "UNKNOWN"

    def test_missing_position_percentage_is_excluded_from_sum(
        self, service
    ):
        holdings = [
            make_holding(
                "AAA", Decimal("60"), "core_equity",
                Decimal("6000"),
            ),
            make_holding(
                "BBB", None, "core_equity",
                Decimal("4000"),
            ),
        ]

        allocations = service._calculate_actual_allocations(
            holdings=holdings,
            bucket_names=["core_equity"],
        )

        assert allocations[0].percentage == Decimal("60")
        assert allocations[0].market_value == Decimal("10000")
        assert len(allocations[0].holdings) == 2

    def test_invalid_bucket_names_raise_value_error(self, service):
        with pytest.raises(
            ValueError, match="bucket_names must be a non-empty list"
        ):
            service._calculate_actual_allocations(
                holdings=[],
                bucket_names=[],
            )

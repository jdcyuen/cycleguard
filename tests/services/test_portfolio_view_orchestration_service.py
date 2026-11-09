
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from models.position import Position
from models.account_config import (
    AccountConfig,
    AccountSettings,
    PositionLimits,
)
from models.portfolio_view import (
    PortfolioAccountView,
    PortfolioHolding,
    PortfolioTargetHolding,
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

class TestTargetAllocationCalculation:
    """Tests for configured target bucket and security allocations."""

    @pytest.fixture
    def account_config(self):
        return AccountConfig(
            name="rollover_ira",
            display_name="Rollover IRA",
            account_type="ira",
            risk_profile="conservative",
            account_number="123456",
            institution="Fidelity",
            bucket_mapping={
                "FZROX": "core_equity",
                "FTEC": "equity_growth",
                "SOXX": "equity_growth",
            },
            bucket_weights={
                "defensive": 0.15,
                "fixed_income": 0.30,
                "tips_ladder": 0.10,
                "core_equity": 0.20,
                "equity_income": 0.10,
                "equity_growth": 0.07,
                "high_beta": 0.03,
                "foreign_equity": 0.03,
                "alternatives": 0.02,
            },
            tolerance=0.05,
            bucket_tolerance=0.02,
            security_targets={
                "FZROX": 0.20,
                "FTEC": 0.05,
                "SOXX": 0.01,
            },
            position_limits=PositionLimits(
                max_position_pct=0.25,
                overrides={},
            ),
            settings=AccountSettings(
                rebalance_frequency="quarterly",
                allow_fractional_shares=True,
                enable_recovery_trims=True,
                enable_dynamic_deployment=True,
            ),
        )

    def test_creates_all_configured_buckets(
        self, service, account_config
    ):
        allocations = service._calculate_target_allocations(
            account_config=account_config,
            bucket_names=list(account_config.bucket_weights),
        )

        assert len(allocations) == 9

        assert [allocation.bucket for allocation in allocations] == [
            "defensive",
            "fixed_income",
            "tips_ladder",
            "core_equity",
            "equity_income",
            "equity_growth",
            "high_beta",
            "foreign_equity",
            "alternatives",
        ]

    def test_converts_bucket_weights_to_percentage_points(
        self, service, account_config
    ):
        allocations = service._calculate_target_allocations(
            account_config=account_config,
            bucket_names=list(account_config.bucket_weights),
        )

        core = next(
            allocation
            for allocation in allocations
            if allocation.bucket == "core_equity"
        )

        assert core.percentage == Decimal("20.00")

    def test_assigns_target_securities_to_configured_buckets(
        self, service, account_config
    ):
        allocations = service._calculate_target_allocations(
            account_config=account_config,
            bucket_names=list(account_config.bucket_weights),
        )

        growth = next(
            allocation
            for allocation in allocations
            if allocation.bucket == "equity_growth"
        )

        assert len(growth.target_holdings) == 2

        targets = {
            holding.symbol: holding
            for holding in growth.target_holdings
        }

        assert targets["FTEC"].bucket == "equity_growth"
        assert targets["FTEC"].target_percentage == Decimal("5.00")

        assert targets["SOXX"].bucket == "equity_growth"
        assert targets["SOXX"].target_percentage == Decimal("1.00")

    def test_preserves_bucket_weight_independently_of_security_targets(
        self, service, account_config
    ):
        allocations = service._calculate_target_allocations(
            account_config=account_config,
            bucket_names=list(account_config.bucket_weights),
        )

        growth = next(
            allocation
            for allocation in allocations
            if allocation.bucket == "equity_growth"
        )

        # The bucket target comes from bucket_weights, not a
        # recalculation based on the sum of security targets.
        assert growth.percentage == Decimal("7.00")

        assert sum(
            (
                holding.target_percentage
                for holding in growth.target_holdings
            ),
            Decimal("0"),
        ) == Decimal("6.00")

    def test_includes_buckets_without_target_securities(
        self, service, account_config
    ):
        allocations = service._calculate_target_allocations(
            account_config=account_config,
            bucket_names=list(account_config.bucket_weights),
        )

        defensive = next(
            allocation
            for allocation in allocations
            if allocation.bucket == "defensive"
        )

        assert defensive.percentage == Decimal("15.00")
        assert defensive.target_holdings == []

    def test_target_holdings_are_independent_of_actual_holdings(
        self, service, account_config
    ):
        allocations = service._calculate_target_allocations(
            account_config=account_config,
            bucket_names=list(account_config.bucket_weights),
        )

        all_targets = [
            holding
            for allocation in allocations
            for holding in allocation.target_holdings
        ]

        assert len(all_targets) == 3
        assert all(
            isinstance(holding, PortfolioTargetHolding)
            for holding in all_targets
        )

class TestBuildAccountView:
    """Tests for account view orchestration."""

    def test_calculates_targets_when_snapshot_is_missing(
        self, service, account_view, monkeypatch
    ):
        account_view.database_account.id = 1

        service.list_accounts = MagicMock(
            return_value=[account_view]
        )

        service.snapshot_repository = MagicMock()
        service.snapshot_repository.get_latest_by_account.return_value = (
            None
        )

        bucket_names = ["core_equity", "fixed_income"]

        service._load_valid_bucket_names = MagicMock(
            return_value=bucket_names
        )

        expected_targets = [
            MagicMock(bucket="core_equity"),
            MagicMock(bucket="fixed_income"),
        ]

        calculate_targets = MagicMock(
            return_value=expected_targets
        )

        monkeypatch.setattr(
            service,
            "_calculate_target_allocations",
            calculate_targets,
        )

        result = service.build_account_view(account_id=1)

        calculate_targets.assert_called_once_with(
            account_config=account_view.account_config,
            bucket_names=bucket_names,
        )

        assert result.target_allocations == expected_targets
        assert result.snapshot is None
        assert result.actual_allocations == []
        assert "No portfolio snapshot" in result.message

    def test_calculates_targets_and_actuals_when_snapshot_exists(
        self, service, account_view, monkeypatch
    ):
        account_view.database_account.id = 1

        service.list_accounts = MagicMock(
            return_value=[account_view]
        )

        snapshot = MagicMock()
        snapshot.id = 123

        service.snapshot_repository = MagicMock()
        service.snapshot_repository.get_latest_by_account.return_value = (
            snapshot
        )

        bucket_names = ["core_equity", "fixed_income"]

        service._load_valid_bucket_names = MagicMock(
            return_value=bucket_names
        )

        holdings = [MagicMock()]
        expected_targets = [MagicMock()]
        expected_actuals = [MagicMock()]

        monkeypatch.setattr(
            service,
            "_add_bucket_mappings_to_positions",
            MagicMock(return_value=holdings),
        )

        monkeypatch.setattr(
            service,
            "_calculate_target_allocations",
            MagicMock(return_value=expected_targets),
        )

        monkeypatch.setattr(
            service,
            "_calculate_actual_allocations",
            MagicMock(return_value=expected_actuals),
        )

        monkeypatch.setattr(
            service,
            "_validate_position_percentages",
            MagicMock(),
        )

        result = service.build_account_view(account_id=1)

        assert result.snapshot is snapshot
        assert result.holdings == holdings
        assert result.target_allocations == expected_targets
        assert result.actual_allocations == expected_actuals

        service._calculate_target_allocations.assert_called_once_with(
            account_config=account_view.account_config,
            bucket_names=bucket_names,
        )

        service._calculate_actual_allocations.assert_called_once_with(
            holdings=holdings,
            bucket_names=bucket_names,
        )
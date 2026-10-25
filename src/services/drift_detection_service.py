
"""
Drift Detection Service
=======================

Purpose
-------
Evaluate portfolio positions and bucket allocations against configured
targets using an existing database snapshot. Return normalized rows for
the Drift Detection dashboard and other potential consumers.

Architecture
------------
The service belongs to CycleGuard's service layer.

    Database snapshot
          |
          v
    PositionRepository
          |
          v
    PortfolioAggregationService
          |
          +------------------------------+
          |                              |
          v                              v
    Position-level data           Bucket allocations
                                         |
                                         v
                              BucketTrimProposalService
                                         |
                                         v
                              DriftDetectionService
                                         |
                                         v
                             Drift result dictionaries
                                         |
                        +----------------+----------------+
                        |                |                |
                        v                v                v
                    Dashboard         CLI/reporting    Other consumers

Responsibilities
----------------
- Validate the requested snapshot identifier.
- Retrieve position and bucket allocation data through the portfolio
  service.
- Calculate position drift against explicitly configured security
  targets.
- Preserve positions without configured security targets and identify
  them as "No target configured".
- Use the account's position tolerance for position status.
- Use the account's bucket tolerance for bucket status.
- Delegate bucket trim calculations to BucketTrimProposalService.
- Return separate position and bucket summary rows.

Non-responsibilities
--------------------
- Importing Fidelity CSV files or creating database snapshots.
- Opening database connections or issuing SQL queries directly.
- Making security-level buy or sell recommendations.
- Implementing bucket trim calculations.
- Rendering Streamlit components or AG Grid tables.
- Persisting proposed actions or executing trades.

Error handling
--------------
Invalid input and invalid portfolio/configuration data raise
ValueError with a useful message. Unexpected dependency or calculation
failures are logged with their traceback and re-raised so callers can
handle the failure appropriately. No failures are silently converted
into zero drift or empty results.
"""

import logging
from decimal import Decimal, InvalidOperation
from typing import Any

from models.account_config import AccountConfig
from services.bucket_trim_proposal_service import (
    BucketTrimProposalService,
)

logger = logging.getLogger(__name__)


class DriftDetectionService:
    """
    Assemble position-level and bucket-level drift results.

    Dependencies are injected so this service can be tested independently
    of database implementations and presentation frameworks.

    Args:
        portfolio_service:
            Provides snapshot positions, bucket allocations, and portfolio
            value through CycleGuard's portfolio service layer.
        account:
            Account-specific targets, bucket mappings, and tolerances.
        bucket_trim_service:
            Optional bucket trim proposal service. When omitted, the
            standard BucketTrimProposalService is constructed.
    """

    def __init__(
        self,
        portfolio_service,
        account: AccountConfig,
        bucket_trim_service=None,
    ) -> None:
        if portfolio_service is None:
            raise ValueError("portfolio_service is required")

        if account is None:
            raise ValueError("account is required")

        self.portfolio_service = portfolio_service
        self.account = account
        self.bucket_trim_service = (
            bucket_trim_service
            if bucket_trim_service is not None
            else BucketTrimProposalService(
                portfolio_service,
                account,
            )
        )

    def evaluate(self, snapshot_id: int) -> list[dict[str, Any]]:
        """
        Evaluate drift using an existing database snapshot.

        This method is read-only with respect to snapshot creation and
        ingestion. It does not import files or persist proposed actions.

        Returns:
            A list of dictionaries containing position rows and separate
            bucket summary rows, suitable for presentation by a dashboard
            or another consumer.

        Raises:
            ValueError:
                If the snapshot identifier, portfolio value, mappings,
                targets, or tolerances are invalid.
            Exception:
                Unexpected dependency or calculation errors are logged
                and re-raised without hiding the original traceback.
        """
        self._validate_snapshot_id(snapshot_id)

        logger.info(
            "Starting drift evaluation: snapshot_id=%s",
            snapshot_id,
        )

        try:
            rows = self._evaluate_snapshot(snapshot_id)

            position_count = sum(
                row["Row Type"] == "Position" for row in rows
            )
            bucket_count = sum(
                row["Row Type"] == "Bucket" for row in rows
            )

            logger.info(
                "Drift evaluation completed: snapshot_id=%s, "
                "position_rows=%s, bucket_rows=%s",
                snapshot_id,
                position_count,
                bucket_count,
            )
            return rows

        except ValueError:
            logger.exception(
                "Drift evaluation rejected due to invalid data or "
                "configuration: snapshot_id=%s",
                snapshot_id,
            )
            raise

        except Exception:
            logger.exception(
                "Unexpected drift evaluation failure: snapshot_id=%s",
                snapshot_id,
            )
            raise

    def _evaluate_snapshot(
        self,
        snapshot_id: int,
    ) -> list[dict[str, Any]]:
        """Build position and bucket rows for one snapshot."""
        positions = self.portfolio_service.get_positions(snapshot_id)

        # This call validates bucket mappings through the aggregation
        # service and returns the account's bucket allocations.
        bucket_allocations = (
            self.portfolio_service.get_bucket_allocation(snapshot_id)
        )

        portfolio_value = self._as_decimal(
            self.portfolio_service.get_portfolio_value(snapshot_id),
            "portfolio value",
        )

        if not portfolio_value.is_finite() or portfolio_value <= 0:
            raise ValueError(
                "Portfolio value must be finite and positive"
            )

        position_targets = self.account.security_targets
        bucket_mapping = self.account.bucket_mapping

        position_tolerance = self._validate_tolerance(
            self.account.tolerance,
            "position tolerance",
        )
        bucket_tolerance = self._validate_tolerance(
            self.account.bucket_tolerance,
            "bucket tolerance",
        )

        # Explicitly check mappings so missing symbols cannot disappear
        # when this service is tested with a substitute portfolio service.
        missing_symbols = sorted(
            {
                position.symbol
                for position in positions
                if bucket_mapping.get(position.symbol) is None
            }
        )
        if missing_symbols:
            config_path = (
                getattr(self.account, "config_path", None)
                or "<account YAML path unavailable>"
            )
            raise ValueError(
                "Missing bucket mappings for symbol(s): "
                f"{', '.join(missing_symbols)}. "
                f"Update account YAML: {config_path}. "
                "Use a valid bucket from src/config/system/buckets.yaml."
            )

        trim_proposals = self.bucket_trim_service.evaluate(snapshot_id)
        proposals_by_bucket = {
            proposal.bucket_name: proposal
            for proposal in trim_proposals
        }

        rows = []

        for position in positions:
            symbol = position.symbol
            bucket = bucket_mapping[symbol]

            market_value = self._as_decimal(
                position.current_value,
                f"market value for {symbol}",
            )
            actual_weight = market_value / portfolio_value

            configured_target = position_targets.get(symbol)

            if configured_target is None:
                target_weight = None
                drift = None
                drift_value = None
                status = "No target configured"
            else:
                target_weight = self._as_decimal(
                    configured_target,
                    f"security target for {symbol}",
                )
                self._validate_target(
                    target_weight,
                    f"security target for {symbol}",
                )

                # Positive drift means overweight; negative means
                # underweight. Drift is a percentage-point difference.
                drift = actual_weight - target_weight
                drift_value = drift * portfolio_value
                status = self._get_status(
                    drift,
                    position_tolerance,
                )

            rows.append(
                {
                    "Row Type": "Position",
                    "Position": symbol,
                    "Bucket": bucket,
                    "Market Value": market_value,
                    "Actual %": actual_weight,
                    "Target %": target_weight,
                    "Drift %": drift,
                    "Drift $": drift_value,
                    "Status": status,
                    "Proposed Action": None,
                    "Proposed Amount": None,
                }
            )

        # Each bucket gets exactly one summary row. The trim amount is
        # displayed on that row, not repeated across its positions.
        for bucket_name, allocation in sorted(
            bucket_allocations.items()
        ):
            actual_weight = self._as_decimal(
                allocation.actual_weight,
                f"actual weight for bucket {bucket_name}",
            )
            target_weight = self._as_decimal(
                allocation.target_weight,
                f"target weight for bucket {bucket_name}",
            )
            market_value = self._as_decimal(
                allocation.market_value,
                f"market value for bucket {bucket_name}",
            )

            drift = actual_weight - target_weight
            drift_value = drift * portfolio_value
            status = self._get_status(drift, bucket_tolerance)

            proposal = proposals_by_bucket.get(bucket_name)
            proposed_action = None
            proposed_amount = None

            if proposal is not None:
                proposed_action = "Trim bucket"
                proposed_amount = self._as_decimal(
                    proposal.trim_amount,
                    f"trim amount for bucket {bucket_name}",
                )

            rows.append(
                {
                    "Row Type": "Bucket",
                    "Position": "Bucket Summary",
                    "Bucket": bucket_name,
                    "Market Value": market_value,
                    "Actual %": actual_weight,
                    "Target %": target_weight,
                    "Drift %": drift,
                    "Drift $": drift_value,
                    "Status": status,
                    "Proposed Action": proposed_action,
                    "Proposed Amount": proposed_amount,
                }
            )

        return rows

    @staticmethod
    def _validate_snapshot_id(snapshot_id: int) -> None:
        """Reject invalid identifiers before accessing dependencies."""
        if (
            isinstance(snapshot_id, bool)
            or not isinstance(snapshot_id, int)
            or snapshot_id <= 0
        ):
            raise ValueError(
                "snapshot_id must be a positive integer"
            )

    @staticmethod
    def _as_decimal(value: Any, description: str) -> Decimal:
        """Convert numeric input to Decimal with a contextual error."""
        try:
            result = Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise ValueError(
                f"Invalid numeric value for {description}: {value!r}"
            ) from exc

        if not result.is_finite():
            raise ValueError(
                f"Non-finite numeric value for {description}"
            )

        return result

    @staticmethod
    def _validate_tolerance(
        value: Any,
        description: str,
    ) -> Decimal:
        """Require a finite tolerance between zero and one."""
        tolerance = DriftDetectionService._as_decimal(
            value,
            description,
        )

        if tolerance < 0 or tolerance > 1:
            raise ValueError(
                f"{description} must be between 0 and 1"
            )

        return tolerance

    @staticmethod
    def _validate_target(
        target: Decimal,
        description: str,
    ) -> None:
        """Require a finite target weight between zero and one."""
        if target < 0 or target > 1:
            raise ValueError(
                f"{description} must be between 0 and 1"
            )

    @staticmethod
    def _get_status(
        drift: Decimal,
        tolerance: Decimal,
    ) -> str:
        """Classify drift using the supplied tolerance."""
        if drift > tolerance:
            return "Overweight"
        if drift < -tolerance:
            return "Underweight"
        return "Within tolerance"

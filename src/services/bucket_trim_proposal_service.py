
import logging
from decimal import Decimal

from engine.allocation.bucket_trim_evaluator import (
    BucketTrimEvaluator,
)
from models.bucket_trim_proposal import BucketTrimProposal

logger = logging.getLogger(__name__)


class BucketTrimProposalService:
    """Create reviewable bucket-level trim proposals."""

    def __init__(
        self,
        portfolio_service,
        account,
        trim_evaluator=None,
    ):
        if portfolio_service is None:
            raise ValueError("Portfolio service is required")

        if account is None:
            raise ValueError("Account configuration is required")

        if trim_evaluator is not None and not callable(
            getattr(trim_evaluator, "calculate_trim_amount", None)
        ):
            raise TypeError(
                "Trim evaluator must provide calculate_trim_amount()"
            )

        self.portfolio_service = portfolio_service
        self.account = account
        self.trim_evaluator = (
            trim_evaluator
            if trim_evaluator is not None
            else BucketTrimEvaluator()
        )

        logger.debug(
            "BucketTrimProposalService initialized: account=%s",
            getattr(account, "name", "<unknown>"),
        )

    def evaluate(
        self,
        snapshot_id: int,
    ) -> list[BucketTrimProposal]:
        """Return trim proposals for buckets above their tolerance boundary."""

        try:
            if (
                isinstance(snapshot_id, bool)
                or not isinstance(snapshot_id, int)
                or snapshot_id <= 0
            ):
                raise ValueError(
                    "Snapshot ID must be a positive integer"
                )

            logger.info(
                "Starting bucket trim proposal evaluation: "
                "snapshot_id=%s",
                snapshot_id,
            )

            portfolio_value = (
                self.portfolio_service.get_portfolio_value(
                    snapshot_id
                )
            )

            if not isinstance(portfolio_value, Decimal):
                raise TypeError(
                    "Portfolio value must be a Decimal"
                )

            if (
                not portfolio_value.is_finite()
                or portfolio_value <= Decimal("0")
            ):
                raise ValueError(
                    "Portfolio value must be finite and positive"
                )

            try:
                raw_tolerance = self.account.bucket_tolerance
                bucket_tolerance = Decimal(str(raw_tolerance))
            except (
                AttributeError,
                TypeError,
                ValueError,
                ArithmeticError,
            ) as exc:
                raise ValueError(
                    "Account bucket tolerance is missing or invalid"
                ) from exc

            if (
                not bucket_tolerance.is_finite()
                or bucket_tolerance < Decimal("0")
                or bucket_tolerance > Decimal("1")
            ):
                raise ValueError(
                    "Bucket tolerance must be finite and between 0 and 1"
                )

            bucket_allocations = (
                self.portfolio_service.get_bucket_allocation(
                    snapshot_id
                )
            )

            if not isinstance(bucket_allocations, dict):
                raise TypeError(
                    "Bucket allocations must be a dictionary"
                )

            proposals = []

            for bucket_name, bucket in bucket_allocations.items():
                trim_amount = (
                    self.trim_evaluator.calculate_trim_amount(
                        bucket=bucket,
                        portfolio_value=portfolio_value,
                        tolerance=bucket_tolerance,
                    )
                )

                if trim_amount <= Decimal("0"):
                    continue

                proposal = BucketTrimProposal(
                    bucket_name=bucket.name,
                    actual_weight=bucket.actual_weight,
                    target_weight=bucket.target_weight,
                    upper_boundary=(
                        bucket.target_weight + bucket_tolerance
                    ),
                    trim_amount=trim_amount,
                )
                proposals.append(proposal)

                logger.info(
                    "Bucket trim proposal created: "
                    "bucket=%s, actual_weight=%s, target_weight=%s, "
                    "upper_boundary=%s, trim_amount=%s",
                    proposal.bucket_name,
                    proposal.actual_weight,
                    proposal.target_weight,
                    proposal.upper_boundary,
                    proposal.trim_amount,
                )

            proposals.sort(
                key=lambda proposal: proposal.bucket_name
            )

            logger.info(
                "Bucket trim proposal evaluation completed: "
                "snapshot_id=%s, portfolio_value=%s, "
                "bucket_count=%s, proposal_count=%s",
                snapshot_id,
                portfolio_value,
                len(bucket_allocations),
                len(proposals),
            )

            return proposals

        except (TypeError, ValueError, ArithmeticError):
            logger.exception(
                "Bucket trim proposal evaluation failed validation "
                "or calculation: snapshot_id=%s",
                snapshot_id,
            )
            raise

        except Exception:
            logger.exception(
                "Unexpected failure during bucket trim proposal "
                "evaluation: snapshot_id=%s",
                snapshot_id,
            )
            raise

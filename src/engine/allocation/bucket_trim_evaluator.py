
import logging
from decimal import Decimal

from models.bucket_allocation import BucketAllocation

logger = logging.getLogger(__name__)


class BucketTrimEvaluator:
    """Calculate the minimum trim needed to restore a bucket
    to its upper tolerance boundary.
    """

    @staticmethod
    def calculate_trim_amount(
        bucket: BucketAllocation,
        portfolio_value: Decimal,
        tolerance: Decimal,
    ) -> Decimal:
        """Return the minimum dollar trim, or zero if no trim is needed.

        Raises:
            TypeError: If numeric inputs are not Decimal instances.
            ValueError: If numeric inputs are invalid.
        """
        try:
            if not isinstance(bucket, BucketAllocation):
                raise TypeError("bucket must be a BucketAllocation")

            if not isinstance(portfolio_value, Decimal):
                raise TypeError("Portfolio value must be a Decimal")

            if (
                not portfolio_value.is_finite()
                or portfolio_value <= Decimal("0")
            ):
                raise ValueError(
                    "Portfolio value must be finite and positive"
                )

            if not isinstance(tolerance, Decimal):
                raise TypeError("Tolerance must be a Decimal")

            if not tolerance.is_finite() or tolerance < Decimal("0"):
                raise ValueError(
                    "Tolerance must be finite and non-negative"
                )

            if (
                not bucket.actual_weight.is_finite()
                or not bucket.target_weight.is_finite()
            ):
                raise ValueError(
                    "Bucket weights must be finite"
                )

            upper_boundary = bucket.target_weight + tolerance
            excess_weight = bucket.actual_weight - upper_boundary

            if excess_weight <= Decimal("0"):
                logger.debug(
                    "No trim required for bucket %s: "
                    "actual weight %s, upper boundary %s",
                    bucket.name,
                    bucket.actual_weight,
                    upper_boundary,
                )
                return Decimal("0")

            trim_amount = (
                excess_weight * portfolio_value
            ).quantize(Decimal("0.01"))

            logger.info(
                "Bucket %s exceeds its upper tolerance boundary. "
                "Actual weight: %s, upper boundary: %s, "
                "proposed minimum trim: $%s",
                bucket.name,
                bucket.actual_weight,
                upper_boundary,
                trim_amount,
            )

            return trim_amount

        except (TypeError, ValueError):
            logger.warning(
                "Invalid input to calculate_trim_amount for bucket %s",
                getattr(bucket, "name", "<unknown>"),
                exc_info=True,
            )
            raise

        except Exception:
            logger.exception(
                "Unexpected failure calculating trim amount for bucket %s",
                getattr(bucket, "name", "<unknown>"),
            )
            raise

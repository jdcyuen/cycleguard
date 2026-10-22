import logging
from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN

from engine.allocation.dynamic_allocation_strategy import DynamicAllocationStrategy
from models.allocation_evaluation import AllocationEvaluation

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class AllocationEngine:
    """Coordinates portfolio allocation evaluation."""
    dynamic_allocation_strategy: DynamicAllocationStrategy

    @staticmethod
    def _validate_target(
        target: Decimal,
        name: str,
    ) -> None:
        logger.info(
            "Validating allocation target: name=%s, target=%s",
            name,
            target,
        )

        if target < Decimal("0") or target > Decimal("1"):
            logger.error(
                "Invalid allocation target: name=%s, target=%s",
                name,
                target,
            )
            raise ValueError(
                f"{name} must be between 0 and 1"
            )

    @staticmethod
    def _validate_non_negative(
        value: Decimal,
        name: str,
    ) -> None:
        logger.info(
            "Validating non-negative value: name=%s, value=%s",
            name,
            value,
        )

        if value < Decimal("0"):
            logger.error(
                "Invalid negative value: name=%s, value=%s",
                name,
                value,
            )
            raise ValueError(
                f"{name} cannot be negative"
            )

    def classify_securities(
        self,
        securities: list[str],
        security_targets: dict[str, float],
    ) -> tuple[list[str], list[str]]:
        """
        Separate securities into explicit-target and dynamic groups.

        Securities listed in security_targets are explicit.
        Securities not listed in security_targets are dynamic.
        """
        logger.info(
            "Classifying securities: security_count=%s, explicit_target_count=%s",
            len(securities),
            len(security_targets),
        )

        explicit = []
        dynamic = []

        for symbol in securities:
            if symbol in security_targets:
                explicit.append(symbol)
                logger.info(
                    "Security classified: symbol=%s, classification=explicit",
                    symbol,
                )
            else:
                dynamic.append(symbol)
                logger.info(
                    "Security classified: symbol=%s, classification=dynamic",
                    symbol,
                )

        logger.info(
            "Security classification completed: explicit_count=%s, dynamic_count=%s",
            len(explicit),
            len(dynamic),
        )

        return explicit, dynamic

    def calculate_remaining_dynamic_target(
        self,
        bucket_target: Decimal,
        explicit_targets: dict[str, Decimal],
    ) -> Decimal:
        """
        Calculate the portion of the bucket target available
        for dynamic securities.

        Explicit security targets consume part of the bucket target.
        The remaining allocation is available to dynamic securities.

        Raises:
            ValueError: If explicit security targets exceed
                the bucket target.
        """
        explicit_total = Decimal("0")

        for symbol, target in explicit_targets.items():
            explicit_total += target

            logger.info(
                "Processing explicit security target: "
                "symbol=%s, target=%s, running_explicit_total=%s",
                symbol,
                target,
                explicit_total,
            )



        if explicit_total > bucket_target:
            logger.error(
                "Explicit security targets exceed bucket target: "
                "explicit_total=%s, bucket_target=%s",
                explicit_total,
                bucket_target,
            )
            raise ValueError(
                "Explicit security targets cannot exceed bucket target"
            )

        remaining_target = bucket_target - explicit_total

        logger.info(
            "Remaining dynamic target calculated: %s",
            remaining_target,
        )

        return remaining_target

    def calculate_dynamic_targets(
        self,
        bucket_target: Decimal,
        explicit_targets: dict[str, Decimal],
        dynamic_securities: dict[str, Decimal],
    ) -> dict[str, Decimal]:
        """
        Calculate desired portfolio-level targets for dynamic securities.

        The remaining bucket allocation, after explicit security targets
        are accounted for, is distributed by the configured dynamic
        allocation strategy.
        """
        remaining_target = self.calculate_remaining_dynamic_target(
            bucket_target=bucket_target,
            explicit_targets=explicit_targets,
        )

        logger.info(
            "Calculating dynamic allocation targets: "
            "bucket_target=%s, remaining_target=%s, "
            "explicit_target_count=%s, dynamic_security_count=%s",
            bucket_target,
            remaining_target,
            len(explicit_targets),
            len(dynamic_securities),
        )

        for symbol, current_value in dynamic_securities.items():
            logger.info(
                "Calculating dynamic target for security: "
                "symbol=%s, current_value=%s, available_target=%s",
                symbol,
                current_value,
                remaining_target,
            )

        try:
            dynamic_targets = self.dynamic_allocation_strategy.allocate(
                available_target=remaining_target,
                securities=dynamic_securities,
            )
        except (ValueError, TypeError) as exc:
            logger.exception(
                "Dynamic allocation strategy failed: "
                "available_target=%s, security_count=%s, securities=%s",
                remaining_target,
                len(dynamic_securities),
                list(dynamic_securities.keys()),
            )
            raise RuntimeError(
                "Dynamic allocation strategy failed"
            ) from exc

        for symbol, target in dynamic_targets.items():
            logger.info(
                "Dynamic target calculated: symbol=%s, target=%s",
                symbol,
                target,
            )

        logger.info(
            "Dynamic allocation targets calculated: "
            "target_count=%s, total_target=%s",
            len(dynamic_targets),
            sum(dynamic_targets.values(), Decimal("0")),
        )

        return dynamic_targets    


    def calculate_security_differences(
        self,
        actual_targets: dict[str, Decimal],
        desired_targets: dict[str, Decimal],
    ) -> dict[str, Decimal]:
        """
        Calculate the difference between desired and actual
        portfolio weights for each security.

        Positive values mean the security is below its desired
        allocation and needs additional allocation.

        Negative values mean the security is above its desired
        allocation.
        """
        logger.info(
            "Calculating security allocation differences: "
            "actual_target_count=%s, desired_target_count=%s",
            len(actual_targets),
            len(desired_targets),
        )

        symbols = set(actual_targets) | set(desired_targets)

        differences = {}

        for symbol in symbols:
            actual_target = actual_targets.get(symbol, Decimal("0"))
            desired_target = desired_targets.get(symbol, Decimal("0"))
            difference = desired_target - actual_target

            logger.info(
                "Security allocation difference: "
                "symbol=%s, actual_target=%s, desired_target=%s, difference=%s",
                symbol,
                actual_target,
                desired_target,
                difference,
            )

            differences[symbol] = difference

        logger.info(
            "Security allocation differences calculated: "
            "security_count=%s",
            len(differences),
        )

        return differences  

    def determine_allocation_status(
        self,
        actual_target: Decimal,
        desired_target: Decimal,
        tolerance: Decimal,
    ) -> str:
        """
        Determine whether a security should be bought, held, or trimmed.

        The tolerance defines the acceptable range around the desired
        allocation.

        Below the lower boundary → BUY
        Within the tolerance range → HOLD
        Above the upper boundary → TRIM
        """
        logger.info(
            "Determining allocation status: "
            "actual_target=%s, desired_target=%s, tolerance=%s",
            actual_target,
            desired_target,
            tolerance,
        )

        lower_bound = max(
            Decimal("0"),
            desired_target - tolerance,
        )
        upper_bound = desired_target + tolerance

        logger.info(
            "Allocation status boundaries calculated: "
            "lower_bound=%s, upper_bound=%s",
            lower_bound,
            upper_bound,
        )

        if actual_target < lower_bound:
            logger.info(
                "Allocation status determined: status=BUY, "
                "actual_target=%s, lower_bound=%s",
                actual_target,
                lower_bound,
            )
            return "BUY"

        if actual_target > upper_bound:
            logger.info(
                "Allocation status determined: status=TRIM, "
                "actual_target=%s, upper_bound=%s",
                actual_target,
                upper_bound,
            )
            return "TRIM"

        logger.info(
            "Allocation status determined: status=HOLD, "
            "actual_target=%s, lower_bound=%s, upper_bound=%s",
            actual_target,
            lower_bound,
            upper_bound,
        )

        return "HOLD"  

    def calculate_security_action_amount(
        self,
        symbol: str,
        actual_target: Decimal,
        desired_target: Decimal,
        tolerance: Decimal,
        portfolio_value: Decimal,
    ) -> Decimal:
        """
        Calculate the dollar amount needed to move a security
        to the applicable tolerance boundary.

        BUY moves the security up to the lower boundary.
        TRIM moves the security down to the upper boundary.
        HOLD produces zero.

        Returns:
            Positive amount for BUY.
            Negative amount for TRIM.
            Zero for HOLD.
        """
        logger.info(
            "Calculating security action amount: "
            "symbol=%s, actual_target=%s, desired_target=%s, "
            "tolerance=%s, portfolio_value=%s",
            symbol,
            actual_target,
            desired_target,
            tolerance,
            portfolio_value,
        )

        status = self.determine_allocation_status(
            actual_target=actual_target,
            desired_target=desired_target,
            tolerance=tolerance,
        )

        lower_bound = max(
            Decimal("0"),
            desired_target - tolerance,
        )
        upper_bound = desired_target + tolerance

        logger.info(
            "Security action boundaries calculated: "
            "symbol=%s, status=%s, lower_bound=%s, upper_bound=%s",
            symbol,
            status,
            lower_bound,
            upper_bound,
        )

        if status == "BUY":
            target_amount = portfolio_value * lower_bound
            actual_amount = portfolio_value * actual_target
            action_amount = target_amount - actual_amount

            logger.info(
                "Security action calculated: "
                "symbol=%s, status=BUY, target_amount=%s, actual_amount=%s, "
                "action_amount=%s",
                symbol,
                target_amount,
                actual_amount,
                action_amount,
            )

            return action_amount

        if status == "TRIM":
            target_amount = portfolio_value * upper_bound
            actual_amount = portfolio_value * actual_target
            action_amount = -(actual_amount - target_amount)

            logger.info(
                "Security action calculated: "
                "symbol=%s, status=TRIM, target_amount=%s, actual_amount=%s, "
                "action_amount=%s",
                symbol,
                target_amount,
                actual_amount,
                action_amount,
            )

            return action_amount

        logger.info(
            "Security action calculated: symbol=%s, status=HOLD, action_amount=0",
            symbol,
        )

        return Decimal("0")

    def _calculate_deployment_needs(
        self,
        actual_targets: dict[str, Decimal],
        desired_targets: dict[str, Decimal],
        portfolio_value: Decimal,
        eligible_securities: list[str],
    ) -> dict[str, Decimal]:
        """Calculate dollar underweight needs for eligible securities."""

        differences = self.calculate_security_differences(
            actual_targets=actual_targets,
            desired_targets=desired_targets,
        )

        needs = {
            symbol: portfolio_value * difference
            for symbol, difference in differences.items()
            if symbol in eligible_securities
            and difference > Decimal("0")
        }

        logger.debug(
            "Calculated deployment needs: %s",
            needs,
        )

        return needs

    @staticmethod
    def _calculate_proportional_allocations(
        amount_to_allocate: Decimal,
        needs: dict[str, Decimal],
        total_need: Decimal,
    ) -> dict[str, Decimal]:
        """Calculate cent-rounded allocations proportional to security need."""

        cent = Decimal("0.01")

        return {
            symbol: (
                amount_to_allocate * (need / total_need)
            ).quantize(cent, rounding=ROUND_DOWN)
            for symbol, need in needs.items()
        }

    @staticmethod
    def _distribute_remainder(
        allocations: dict[str, Decimal],
        needs: dict[str, Decimal],
        remainder: Decimal,
    ) -> dict[str, Decimal]:
        """Distribute remaining cents without exceeding security need."""

        cent = Decimal("0.01")

        while remainder >= cent:
            eligible_for_remainder = {
                symbol: need - allocations[symbol]
                for symbol, need in needs.items()
                if need - allocations[symbol] >= cent
            }

            if not eligible_for_remainder:
                break

            symbol = max(
                eligible_for_remainder,
                key=eligible_for_remainder.get,
            )

            allocations[symbol] += cent
            remainder -= cent

        return allocations

    def allocate_deployment(
        self,
        deployment_amount: Decimal,
        actual_targets: dict[str, Decimal],
        desired_targets: dict[str, Decimal],
        portfolio_value: Decimal,
        eligible_securities: list[str],
    ) -> dict[str, Decimal]:
        """
        Distribute approved deployment capital across eligible underweight securities.
        """

        logger.info(
            "Allocating deployment: amount=%s, portfolio_value=%s, "
            "eligible_security_count=%s",
            deployment_amount,
            portfolio_value,
            len(eligible_securities)
            if isinstance(eligible_securities, list)
            else "invalid",
        )

        try:
            if not isinstance(deployment_amount, Decimal):
                raise TypeError("Deployment amount must be a Decimal")

            if not deployment_amount.is_finite():
                raise ValueError("Deployment amount must be finite")

            if not isinstance(portfolio_value, Decimal):
                raise TypeError("Portfolio value must be a Decimal")

            if not portfolio_value.is_finite():
                raise ValueError("Portfolio value must be finite")

            self._validate_non_negative(
                deployment_amount,
                "Deployment amount",
            )
            self._validate_non_negative(
                portfolio_value,
                "Portfolio value",
            )

            if not isinstance(actual_targets, dict):
                raise TypeError("Actual targets must be a dictionary")

            if not isinstance(desired_targets, dict):
                raise TypeError("Desired targets must be a dictionary")

            if not isinstance(eligible_securities, list):
                raise TypeError("Eligible securities must be a list")

            if deployment_amount == Decimal("0"):
                logger.info(
                    "Deployment amount is zero; no allocation required"
                )
                return {}

            if portfolio_value == Decimal("0"):
                logger.info(
                    "Portfolio value is zero; no allocation possible"
                )
                return {}

            needs = self._calculate_deployment_needs(
                actual_targets=actual_targets,
                desired_targets=desired_targets,
                portfolio_value=portfolio_value,
                eligible_securities=eligible_securities,
            )

            if not needs:
                logger.info(
                    "No eligible underweight securities found; "
                    "deployment amount=%s remains unallocated",
                    deployment_amount,
                )
                return {}

            total_need = sum(needs.values(), Decimal("0"))
            amount_to_allocate = min(
                deployment_amount,
                total_need,
            )

            allocations = self._calculate_proportional_allocations(
                amount_to_allocate=amount_to_allocate,
                needs=needs,
                total_need=total_need,
            )

            allocated_total = sum(
                allocations.values(),
                Decimal("0"),
            )

            remainder = (
                amount_to_allocate.quantize(Decimal("0.01"))
                - allocated_total
            )

            allocations = self._distribute_remainder(
                allocations=allocations,
                needs=needs,
                remainder=remainder,
            )

            actual_allocated = sum(
                allocations.values(),
                Decimal("0"),
            )

            logger.info(
                "Deployment allocation completed: approved=%s, "
                "allocated=%s, unallocated=%s, security_count=%s",
                deployment_amount,
                actual_allocated,
                deployment_amount - actual_allocated,
                len(allocations),
            )

            logger.debug(
                "Deployment allocation details: %s",
                allocations,
            )

            return allocations

        except (TypeError, ValueError, ArithmeticError) as exc:
            logger.exception(
                "Failed to allocate deployment: amount=%s",
                deployment_amount,
            )
            raise ValueError("Failed to allocate deployment") from exc

    def evaluate_allocation(
        self,
        top_level_targets: dict[str, Decimal],
        bucket_targets: dict[str, Decimal],
        bucket_target: Decimal,
        explicit_security_targets: dict[str, Decimal],
        dynamic_securities: dict[str, Decimal],
    ) -> AllocationEvaluation:
        """
        Build the desired allocation for a portfolio.

        Explicit security targets are preserved and the remaining
        bucket allocation is distributed among dynamic securities
        using the configured dynamic allocation strategy.
        """
        logger.info(
            "Evaluating portfolio allocation: bucket_target=%s, explicit_security_count=%s, dynamic_security_count=%s",
            bucket_target,
            len(explicit_security_targets),
            len(dynamic_securities),
        )

        try:
            dynamic_targets = self.calculate_dynamic_targets(
                bucket_target=bucket_target,
                explicit_targets=explicit_security_targets,
                dynamic_securities=dynamic_securities,
            )
        except (ValueError, TypeError) as exc:
            logger.exception(
                "Failed to calculate dynamic allocation targets: "
                "bucket_target=%s, explicit_security_count=%s, dynamic_security_count=%s",
                bucket_target,
                len(explicit_security_targets),
                len(dynamic_securities),
            )
            raise RuntimeError("Failed to calculate dynamic allocation targets") from exc

        security_targets = {
            **explicit_security_targets,
            **dynamic_targets,
        }

        for symbol, target in security_targets.items():
            classification = (
                "explicit"
                if symbol in explicit_security_targets
                else "dynamic"
            )

            logger.info(
                "Security allocation target finalized: "
                "symbol=%s, classification=%s, target=%s",
                symbol,
                classification,
                target,
            )

        evaluation = AllocationEvaluation(
            top_level_targets=top_level_targets,
            bucket_targets=bucket_targets,
            security_targets=security_targets,
        )

        logger.info(
            "Allocation evaluation completed: top_level_targets=%s, bucket_targets=%s, security_targets=%s",
            evaluation.top_level_targets,
            evaluation.bucket_targets,
            evaluation.security_targets,
        )

        return evaluation
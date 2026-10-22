import logging
from decimal import Decimal

from models.trade import Trade
from models.trade_plan import TradePlan

logger = logging.getLogger(__name__)


class TradePlanner:
    """Creates immutable trade plans from proposed buys and sells."""

    def create_plan(
        self,
        deployment_amount: Decimal,
        buys: dict[str, Decimal],
        sells: dict[str, Decimal],
        reason: str,
    ) -> TradePlan:
        """Create a TradePlan from proposed buy and sell amounts."""

        logger.info(
            "Creating trade plan: deployment_amount=%s, "
            "buy_count=%s, sell_count=%s, reason=%s",
            deployment_amount,
            len(buys),
            len(sells),
            reason,
        )

        try:
            self._validate_inputs(
                deployment_amount,
                buys,
                sells,
                reason,
            )

            buy_trades = self._create_trades(
                buys,
                "BUY",
            )

            sell_trades = self._create_trades(
                sells,
                "SELL",
            )

            plan = TradePlan(
                deployment_amount=deployment_amount,
                sells=sell_trades,
                buys=buy_trades,
                reason=reason,
            )

            logger.info(
                "Trade plan created: buy_count=%s, sell_count=%s",
                len(plan.buys),
                len(plan.sells),
            )

            return plan

        except (TypeError, ValueError) as exc:
            logger.exception(
                "Failed to create trade plan: "
                "deployment_amount=%s, reason=%s",
                deployment_amount,
                reason,
            )
            raise ValueError("Invalid trade plan inputs") from exc

    @staticmethod
    def _validate_inputs(
        deployment_amount: Decimal,
        buys: dict[str, Decimal],
        sells: dict[str, Decimal],
        reason: str,
    ) -> None:
    
        if not isinstance(deployment_amount, Decimal):
            raise TypeError("Deployment amount must be a Decimal")

        if not deployment_amount.is_finite():
            raise ValueError("Deployment amount must be finite")

        if deployment_amount < Decimal("0"):
            raise ValueError("Deployment amount cannot be negative")

        if not isinstance(buys, dict):
            raise TypeError("Buys must be a dictionary")

        if not isinstance(sells, dict):
            raise TypeError("Sells must be a dictionary")

        conflicting_symbols = set(buys) & set(sells)

        if conflicting_symbols:
            raise ValueError(
                "A symbol cannot have both BUY and SELL trades: "
                f"{sorted(conflicting_symbols)}"
            )

        if not isinstance(reason, str):
            raise TypeError("Reason must be a string")

        if not reason.strip():
            raise ValueError("Reason cannot be empty")

        for trade_group in (buys, sells):
            for symbol, amount in trade_group.items():

                if not isinstance(symbol, str) or not symbol.strip():
                    raise ValueError(
                        "Trade symbol cannot be empty"
                    )

                if not isinstance(amount, Decimal):
                    raise TypeError(
                        f"Trade amount must be a Decimal: {symbol}"
                    )

                if not amount.is_finite():
                    raise ValueError(
                        f"Trade amount must be finite: {symbol}"
                    )

                if amount <= Decimal("0"):
                    raise ValueError(
                        f"Trade amount must be greater than zero: {symbol}"
                    )
        if buys:
            buy_total = sum(buys.values(), Decimal("0"))

            if buy_total != deployment_amount:
                raise ValueError(
                    "Total BUY amount must equal deployment amount"
                )

    @staticmethod
    def _create_trades(
        trades: dict[str, Decimal],
        action: str,
    ) -> tuple[Trade, ...]:
        return tuple(
            Trade(
                symbol=symbol,
                action=action,
                amount=amount,
            )
            for symbol, amount in trades.items()
        )
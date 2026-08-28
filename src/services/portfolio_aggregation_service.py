from decimal import Decimal

from models.account_config import AccountConfig
from models.bucket_allocation import BucketAllocation
from models.portfolio_bucket import PortfolioBucket
from models.position_allocation import PositionAllocation
from models.portfolio_allocation import PortfolioAllocation

from repositories.position_repo import PositionRepository


class PortfolioAggregationService:
    """
    Aggregates portfolio positions into bucket-level results.
    """

    def __init__(
        self,
        position_repository: PositionRepository,
        account: AccountConfig,
    ):
        self.position_repository = position_repository
        self.account = account

    def get_positions(
        self,
        snapshot_id: int,
    ):
        """
        Retrieve positions with security information for a snapshot.
        """
        return self.position_repository.get_by_snapshot_with_security(
            snapshot_id
        )
    
    def get_bucket_mapping(self) -> dict:
        """
        Return the bucket mapping for the account.
        """
        return self.account.bucket_mapping

    def map_positions_to_buckets(
        self,
        snapshot_id: int,
    ) -> dict[str, list]:

        """
        Group positions by their configured bucket.
        """

        positions = self.get_positions(snapshot_id)
        bucket_mapping = self.get_bucket_mapping()

        buckets: dict[str, list] = {}

        for position in positions:
            bucket = bucket_mapping.get(position.symbol)

            if bucket is None:
                raise ValueError(
                    f"No bucket mapping found for symbol "
                    f"{position.symbol}"
                )

            buckets.setdefault(bucket, []).append(position)

        return buckets

    def calculate_bucket_values(
        self,
        snapshot_id: int,
    ) -> dict[str, Decimal]:
        """
        Calculate the total market value for each bucket.
        """

        buckets = self.map_positions_to_buckets(snapshot_id)

        return {
            bucket: sum(
                position.current_value
                for position in positions
            )
            for bucket, positions in buckets.items()
        }

    def calculate_position_bucket_weights(
        self,
        snapshot_id: int,
    ) -> dict[str, list[PositionAllocation]]:

        """
        Calculate each position's weight within its bucket.
        """
        buckets = self.map_positions_to_buckets(
            snapshot_id
        )

        result: dict[str, list[PositionAllocation]] = {}

        for bucket, positions in buckets.items():
            bucket_value = sum(
                position.current_value
                for position in positions
            )

            if bucket_value == 0:
                result[bucket] = [
                    PositionAllocation(
                        symbol=position.symbol,
                        bucket=bucket,
                        market_value=position.current_value,
                        weight=Decimal("0"),
                    )
                    for position in positions
                ]
                continue

            result[bucket] = [
                PositionAllocation(
                    symbol=position.symbol,
                    bucket=bucket,
                    market_value=position.current_value,
                    weight=(
                        position.current_value / bucket_value
                    ),
                )
                for position in positions
            ]

        return result
        

    def calculate_portfolio_value(
        self,
        snapshot_id: int,
    ) -> Decimal:

        """
        Calculate the total market value of the portfolio.
        """

        positions = self.get_positions(snapshot_id)

        return sum(
            position.current_value
            for position in positions
        )

    def get_portfolio_value(
        self,
        snapshot_id: int,
    ) -> Decimal:

        """
        Return the total market value of the portfolio.
        """
        return self.calculate_portfolio_value(snapshot_id)

    def calculate_bucket_weights(
        self,
        snapshot_id: int,
    ) -> dict[str, Decimal]:

        """
        Calculate each bucket's actual weight in the portfolio.
        """

        bucket_values = self.calculate_bucket_values(snapshot_id)
        portfolio_value = self.calculate_portfolio_value(snapshot_id)

        if portfolio_value == 0:
            return {
                bucket: Decimal("0")
                for bucket in bucket_values
            }

        return {
            bucket: value / portfolio_value
            for bucket, value in bucket_values.items()
        }

    def get_target_weights(
        self,
    ) -> dict[str, Decimal]:

        """
        Return the configured target weight for each bucket.
        """
        return self.account.bucket_weights

    def get_bucket_allocation(
        self,
        snapshot_id: int,
    ) -> dict[str, BucketAllocation]:

        """
        Return actual, target, and drift information for each bucket.
        """

        positions = self.get_positions(snapshot_id)

        bucket_mapping = self.get_bucket_mapping()

        buckets: dict[str, list] = {}

        for position in positions:
            bucket = bucket_mapping.get(position.symbol)

            if bucket is None:
                raise ValueError(
                    f"No bucket mapping found for symbol "
                    f"{position.symbol}"
                )

            buckets.setdefault(bucket, []).append(position)

        portfolio_value = sum(
            position.current_value
            for position in positions
        )

        target_weights = self.get_target_weights()

        if portfolio_value == 0:
            actual_weights = {
                bucket: Decimal("0")
                for bucket in buckets
            }
        else:
            actual_weights = {
                bucket: sum(
                    position.current_value
                    for position in bucket_positions
                ) / portfolio_value
                for bucket, bucket_positions in buckets.items()
            }

        bucket_names = set(actual_weights) | set(target_weights)

        return {
            bucket: BucketAllocation(
                name=bucket,
                market_value=sum(
                    position.current_value
                    for position in buckets.get(bucket, [])
                ),
                actual_weight=actual_weights.get(
                    bucket,
                    Decimal("0"),
                ),
                target_weight=target_weights.get(
                    bucket,
                    Decimal("0"),
                ),
                drift=(
                    actual_weights.get(
                        bucket,
                        Decimal("0"),
                    )
                    - target_weights.get(
                        bucket,
                        Decimal("0"),
                    )
                ),
                drift_value=(
                    actual_weights.get(
                        bucket,
                        Decimal("0"),
                    )
                    - target_weights.get(
                        bucket,
                        Decimal("0"),
                    )
                ) * portfolio_value,
            )
            for bucket in bucket_names
        }

    def get_portfolio_allocation(
        self,
        snapshot_id: int,
    ) -> PortfolioAllocation:
        """
        Return the complete aggregated portfolio allocation.
        """
        portfolio_value = self.get_portfolio_value(
            snapshot_id
        )

        buckets = self.get_bucket_allocation(
            snapshot_id
        )

        return PortfolioAllocation(
            portfolio_value=portfolio_value,
            buckets=buckets,
        )
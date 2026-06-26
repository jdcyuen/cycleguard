import psycopg


class PositionRepositoryError(Exception):
    """Raised when position repository operations fail."""

class PositionRepository:
    def __init__(self, conn):
        self.conn = conn

    def insert(
        self,
        snapshot_id: int,
        account_id: int,
        security_id: int,
        quantity=None,
        avg_cost=None,
        cost_basis_total=None,
        market_value=None,
        percent_of_account=None,
        daily_gain=None,
        daily_gain_pct=None,
        total_gain=None,
        total_gain_pct=None,
    ):
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO positions (
                        snapshot_id,
                        account_id,
                        security_id,
                        quantity,
                        avg_cost,
                        cost_basis_total,
                        market_value,
                        percent_of_account,
                        daily_gain,
                        daily_gain_pct,
                        total_gain,
                        total_gain_pct
                    )
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        snapshot_id,
                        account_id,
                        security_id,
                        quantity,
                        avg_cost,
                        cost_basis_total,
                        market_value,
                        percent_of_account,
                        daily_gain,
                        daily_gain_pct,
                        total_gain,
                        total_gain_pct,
                    ),
                )

            self.conn.commit()

        except psycopg.IntegrityError as exc:
            self.conn.rollback()

            raise PositionRepositoryError(
                f"Position already exists for "
                f"snapshot_id={snapshot_id}, "
                f"security_id={security_id}"
            ) from exc

        except psycopg.Error as exc:
            self.conn.rollback()

            raise PositionRepositoryError(
                f"Failed to insert position "
                f"for security_id={security_id}"
            ) from exc
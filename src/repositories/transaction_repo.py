from typing import Optional

import psycopg

from core.logger import get_logger

logger = get_logger(__name__)


class TransactionRepositoryError(Exception):
    """Raised when transaction repository operations fail."""


class TransactionRepository:
    """
    Repository for cycleguard.transactions table.
    """

    def __init__(
        self,
        conn,
    ):
        self.conn = conn

    def insert(
        self,
        account_id: int,
        security_id: Optional[int],
        run_date,
        settlement_date,
        action: str,
        trade_type: str,
        price,
        quantity,
        commission,
        fees,
        accrued_interest,
        amount,
        cash_balance,
    ) -> int:
        """
        Insert a transaction record.

        Returns:
            transaction id
        """

        sql = """
            INSERT INTO cycleguard.transactions
            (
                account_id,
                security_id,
                run_date,
                settlement_date,
                action,
                trade_type,
                price,
                quantity,
                commission,
                fees,
                accrued_interest,
                amount,
                cash_balance
            )
            VALUES
            (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s
            )
            RETURNING id;
        """

        try:
            with self.conn.cursor() as cur:

                cur.execute(
                    sql,
                    (
                        account_id,
                        security_id,
                        run_date,
                        settlement_date,
                        action,
                        trade_type,
                        price,
                        quantity,
                        commission,
                        fees,
                        accrued_interest,
                        amount,
                        cash_balance,
                    ),
                )

                transaction_id = cur.fetchone()[0]

            self.conn.commit()

            logger.debug(
                f"Inserted transaction "
                f"id={transaction_id}"
            )

            return transaction_id

        except psycopg.IntegrityError as exc:
            self.conn.rollback()

            logger.error(
                "Transaction integrity error",
                exc_info=True,
            )

            raise TransactionRepositoryError(
                "Transaction already exists "
                f"for account_id={account_id}"
            ) from exc

        except psycopg.Error as exc:
            self.conn.rollback()

            logger.error(
                "Transaction database error",
                exc_info=True,
            )

            raise TransactionRepositoryError(
                "Failed to insert transaction "
                f"for account_id={account_id}"
            ) from exc

    def exists(
        self,
        account_id: int,
        run_date,
        security_id: Optional[int],
        amount,
        action: str,
        trade_type: str,
    ) -> bool:
        """
        Check if transaction already exists.

        Used for duplicate protection.
        """

        sql = """
            SELECT 1
            FROM cycleguard.transactions
            WHERE account_id = %s
              AND run_date = %s
              AND security_id IS NOT DISTINCT FROM %s
              AND amount = %s
              AND action = %s
              AND trade_type = %s
            LIMIT 1;
        """

        try:
            with self.conn.cursor() as cur:

                cur.execute(
                    sql,
                    (
                        account_id,
                        run_date,
                        security_id,
                        amount,
                        action,
                        trade_type,
                    ),
                )

                return cur.fetchone() is not None

        except psycopg.Error as exc:
            logger.error(
                "Transaction lookup failed",
                exc_info=True,
            )

            raise TransactionRepositoryError(
                "Failed to check transaction existence "
                f"for account_id={account_id}"
            ) from exc
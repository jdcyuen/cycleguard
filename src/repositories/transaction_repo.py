from genericpath import exists
from config import account_config_loader
from models.transaction import Transaction
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
        transaction: Transaction,
    ) -> Transaction:
    
        """
        Insert a transaction record.

        Returns:
             Transaction with its generated id populated.
        """
        
        logger.info(
            "Inserting transaction "
            "account_id=%s "
            "symbol=%s "
            "run_date=%s "
            "action=%s",
            transaction.account_id,
            transaction.symbol,
            transaction.run_date,
            transaction.action,
            transaction.import_history_id,
        )
        logger.debug(
            "run_date=%r (%s)",
            transaction.run_date,
            type(transaction.run_date),
        )

        logger.debug(
            "settlement_date=%r (%s)",
            transaction.settlement_date,
            type(transaction.settlement_date),
        )

        logger.debug(
            "Transaction: %s",
            transaction,
        )     

        try:
            with self.conn.cursor() as cur:

                logger.debug(
                    "run_date=%r (%s)",
                    transaction.run_date,
                    type(transaction.run_date),
                )

                logger.debug(
                    "settlement_date=%r (%s)",
                    transaction.settlement_date,
                    type(transaction.settlement_date),
                )
                params = (
                    transaction.import_history_id,
                    transaction.account_id,
                    transaction.security_id,
                    transaction.run_date,
                    transaction.settlement_date,
                    transaction.action,
                    transaction.trade_type,
                    transaction.price,
                    transaction.quantity,
                    transaction.commission,
                    transaction.fees,
                    transaction.accrued_interest,
                    transaction.amount,
                    transaction.cash_balance,
                )

                logger.debug("SQL parameters: %r", params)

                cur.execute(
                    """
                    INSERT INTO cycleguard.transactions
                    (
                        import_history_id,
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
                        %s,%s, %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s, %s, %s
                    )
                    RETURNING id
                    """,
                    (
                        transaction.import_history_id,
                        transaction.account_id,
                        transaction.security_id,
                        transaction.run_date,
                        transaction.settlement_date,
                        transaction.action,
                        transaction.trade_type,
                        transaction.price,
                        transaction.quantity,
                        transaction.commission,
                        transaction.fees,
                        transaction.accrued_interest,
                        transaction.amount,
                        transaction.cash_balance,
                    ),
                )

                transaction_id = cur.fetchone()[0]

            logger.info(
                f"Transaction inserted successfully for account_id={transaction.account_id}"
            )

            return Transaction(
                id=transaction_id,
                account_id=transaction.account_id,
                security_id=transaction.security_id,
                symbol=transaction.symbol,
                run_date=transaction.run_date,
                settlement_date=transaction.settlement_date,
                action=transaction.action,
                trade_type=transaction.trade_type,
                price=transaction.price,
                quantity=transaction.quantity,
                commission=transaction.commission,
                fees=transaction.fees,
                accrued_interest=transaction.accrued_interest,
                amount=transaction.amount,
                cash_balance=transaction.cash_balance,
                import_history_id=transaction.import_history_id,
            )

        except psycopg.IntegrityError as exc:
            logger.error(
                "Transaction integrity error",
                exc_info=True,
            )

            raise TransactionRepositoryError(
                "Transaction already exists "
                f"for account_id={transaction.account_id}"
            ) from exc

        except psycopg.Error as exc:
            logger.error(
                "Transaction database error",
                exc_info=True,
            )

            raise TransactionRepositoryError(
                "Failed to insert transaction "
                f"for account_id={transaction.account_id}"
            ) from exc


    def exists(
        self,
        transaction: Transaction,
    ) -> bool:

        """
        
        Returns True if an equivalent transaction already exists.

        Duplicate transactions are identified by:

            • account_id
            • run_date
            • security_id
            • amount
            • action
            • trade_type
            
        """

        logger.info(
            "Checking for existing transaction "
            "account_id=%s "
            "symbol=%s "
            "run_date=%s",
            transaction.account_id,
            transaction.symbol,
            transaction.run_date,
        )

        logger.debug(
            "Transaction: %s",
            transaction,
        )

        try:
            with self.conn.cursor() as cur:

                cur.execute(
                     """
                    SELECT EXISTS (
                        SELECT 1
                        FROM cycleguard.transactions
                        WHERE account_id = %s
                        AND run_date = %s
                        AND security_id IS NOT DISTINCT FROM %s
                        AND amount = %s
                        AND action = %s
                        AND trade_type = %s
                    )
                    """,
                    (
                        transaction.account_id,
                        transaction.run_date,
                        transaction.security_id,
                        transaction.amount,
                        transaction.action,
                        transaction.trade_type,
                    ),
                )

                row = cur.fetchone()
                exists = bool(row[0]) if row else False

                if exists:
                    logger.info("Duplicate transaction found.")
                else:
                    logger.info("No duplicate transaction found.")

                return exists

        except psycopg.Error as exc:
            logger.exception("Failed checking transaction existence.")

            raise TransactionRepositoryError(
                "Failed to check transaction existence "
                f"for account_id={transaction.account_id}"
            ) from exc

    def get_by_id(
        self,
        transaction_id: int,
    ) -> Optional[Transaction]:
        """
        Returns the transaction with the specified id,
        or None if it does not exist.
        """

        logger.info(
            "Looking up transaction id=%s",
            transaction_id,
        )

        try:

            with self.conn.cursor() as cur:

                cur.execute(
                    """
                    SELECT
                        id,
                        import_history_id,
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
                    FROM cycleguard.transactions
                    WHERE id = %s
                    """,
                    (transaction_id,),
                )

                row = cur.fetchone()

                if row is None:

                    logger.info(
                        "Transaction id=%s not found.",
                        transaction_id,
                    )

                    return None

                logger.info(
                    "Found transaction id=%s",
                    transaction_id,
                )

                return Transaction(
                    id=row[0],
                    import_history_id=row[1],
                    account_id=row[2],
                    security_id=row[3],
                    run_date=row[4],
                    settlement_date=row[5],
                    action=row[6],
                    trade_type=row[7],
                    price=row[8],
                    quantity=row[9],
                    commission=row[10],
                    fees=row[11],
                    accrued_interest=row[12],
                    amount=row[13],
                    cash_balance=row[14],
                )

        except psycopg.Error as exc:

            logger.exception(
                "Failed retrieving transaction id=%s",
                transaction_id,
            )

            raise TransactionRepositoryError(
                f"Failed retrieving transaction id={transaction_id}"
            ) from exc

    def list_for_account(
        self,
        account_id: int,
    ) -> list[Transaction]:
    
        """
        Returns all transactions for an account,
        ordered by run date.
        """

        logger.info(
            "Retrieving transactions for account_id=%s",
            account_id,
        )

        try:

            with self.conn.cursor() as cur:

                cur.execute(
                    """
                    SELECT
                        id,
                        import_history_id,
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
                    FROM cycleguard.transactions
                    WHERE account_id = %s
                    ORDER BY run_date, id
                    """,
                    (account_id,),
                )

                rows = cur.fetchall()

                logger.info(
                    "Retrieved %d transactions.",
                    len(rows),
                )

                return [
                    Transaction(
                        id=row[0],
                        import_history_id=row[1],
                        account_id=row[2],
                        security_id=row[3],
                        run_date=row[4],
                        settlement_date=row[5],
                        action=row[6],
                        trade_type=row[7],
                        price=row[8],
                        quantity=row[9],
                        commission=row[10],
                        fees=row[11],
                        accrued_interest=row[12],
                        amount=row[13],
                        cash_balance=row[14],
                    )
                    for row in rows
                ]

        except psycopg.Error as exc:

            logger.exception(
                "Failed retrieving transactions for account_id=%s",
                account_id,
            )

            raise TransactionRepositoryError(
                f"Failed retrieving transactions for account_id={account_id}"
            ) from exc

    def delete_by_import_history_id(
        self,
        import_history_id: int,
        ) -> int:
        
        """
        Deletes all transactions created by the specified import.

        ```
        Args:
            import_history_id: ID of the import history record.

        Returns:
            Number of transactions deleted.

        Raises:
            TransactionRepositoryError:
                If the delete operation fails.
        """

        sql = """
            DELETE FROM cycleguard.transactions
            WHERE import_history_id = %s;
        """

        logger.info(
            "Deleting transactions for import_history_id=%s",
            import_history_id,
        )

        try:
            with self.conn.cursor() as cur:

                cur.execute(
                    sql,
                    (import_history_id,),
                )

                rows_deleted = cur.rowcount

            logger.info(
                "Deleted %s transaction(s) "
                "for import_history_id=%s",
                rows_deleted,
                import_history_id,
            )

            return rows_deleted

        except Exception as exc:

            logger.exception(
                "Failed deleting transactions "
                "for import_history_id=%s",
                import_history_id,
            )

            raise TransactionRepositoryError(
                "Unable to delete transactions "
                f"for import_history_id={import_history_id}"
            ) from exc

    def count_by_import_history_id(
        self,
        import_history_id: int,
    ) -> int:
        """
        Returns the number of transactions created by the specified import.
        """

        sql = """
            SELECT COUNT(*)
            FROM cycleguard.transactions
            WHERE import_history_id = %s
        """

        logger.info(
            "Counting transactions for import_history_id=%s",
            import_history_id,
        )

        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    sql,
                    (import_history_id,),
                )

                row = cur.fetchone()

            count = row[0]

            logger.debug(
                "Found %s transaction(s) for import_history_id=%s",
                count,
                import_history_id,
            )

            return count

        except psycopg.Error as exc:
            logger.exception(
                "Failed counting transactions "
                "for import_history_id=%s",
                import_history_id,
            )

            raise TransactionRepositoryError(
                "Unable to count transactions "
                f"for import_history_id={import_history_id}"
            ) from exc

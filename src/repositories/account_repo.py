from typing import Optional
import psycopg
import textwrap


class AccountRepositoryError(Exception):
    """Raised when account repository operations fail."""

class AccountRepository:
    def __init__(self, conn):
        self.conn = conn

    def get_by_number(self, account_number: str) -> Optional[int]:
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    textwrap.dedent(
                        """
                        SELECT id
                        FROM accounts
                        WHERE account_number = %s
                        """
                    ),
                    (account_number,),
                )

                row = cur.fetchone()

                return row[0] if row else None

        except psycopg.Error as exc:
            raise AccountRepositoryError(
                f"Failed to lookup account '{account_number}'"
            ) from exc

    def create(
        self, account_number: str, account_name: str, provider: str = "unknown"
    ) -> int:
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO accounts (
                        account_number,
                        account_name,
                        provider
                    )
                    VALUES (%s, %s, %s)
                    RETURNING id
                    """,
                    (
                        account_number,
                        account_name,
                        provider,
                    ),
                )

                account_id = cur.fetchone()[0]

                self.conn.commit()

                return account_id

        except psycopg.IntegrityError as exc:
            self.conn.rollback()

            raise AccountRepositoryError(
                f"Account '{account_number}' already exists"
            ) from exc

        except psycopg.Error as exc:
            self.conn.rollback()

            raise AccountRepositoryError(
                f"Failed to create account '{account_number}'"
            ) from exc

    def get_or_create(
        self, account_number: str, account_name: str, provider: str = "unknown"
    ) -> int:
        try:
            existing = self.get_by_number(
                account_number
            )

            if existing:
                return existing

            return self.create(
                account_number,
                account_name,
                provider,
            )

        except AccountRepositoryError:
            raise

from typing import Optional


class AccountRepository:
    def __init__(self, conn):
        self.conn = conn

    def get_by_number(self, account_number: str) -> Optional[int]:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT id
                FROM accounts
                WHERE account_number = %s
                """,
                (account_number,),
            )
            row = cur.fetchone()
            return row[0] if row else None

    def create(
        self, account_number: str, account_name: str, provider: str = "unknown"
    ) -> int:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO accounts (account_number, account_name, provider)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (account_number, account_name, provider),
            )
            account_id = cur.fetchone()[0]
            self.conn.commit()
            return account_id

    def get_or_create(
        self, account_number: str, account_name: str, provider: str = "unknown"
    ) -> int:
        existing = self.get_by_number(account_number)

        if existing:
            return existing

        return self.create(account_number, account_name, provider)

from typing import Optional


class SecurityRepository:
    def __init__(self, conn):
        self.conn = conn

    def get_by_ticker(self, ticker: str) -> Optional[int]:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT id
                FROM securities
                WHERE ticker = %s
                """,
                (ticker,),
            )
            row = cur.fetchone()
            return row[0] if row else None

    def create(
        self, ticker: str, description: str = None, asset_type: str = None
    ) -> int:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO securities (ticker, description, asset_type)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (ticker, description, asset_type),
            )
            sec_id = cur.fetchone()[0]
            self.conn.commit()
            return sec_id

    def get_or_create(
        self, ticker: str, description: str = None, asset_type: str = None
    ) -> int:
        existing = self.get_by_ticker(ticker)

        if existing:
            return existing

        return self.create(ticker, description, asset_type)

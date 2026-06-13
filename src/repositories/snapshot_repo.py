from typing import Optional


class SnapshotRepository:
    def __init__(self, conn):
        self.conn = conn

    def get_by_date(self, snapshot_date) -> Optional[int]:
        """
        Returns snapshot_id if exists, else None
        """
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT id
                FROM snapshots
                WHERE snapshot_date = %s
                """,
                (snapshot_date,),
            )
            row = cur.fetchone()
            return row[0] if row else None

    def create(self, snapshot_date) -> int:
        """
        Creates snapshot and returns snapshot_id
        """
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO snapshots(snapshot_date)
                VALUES (%s)
                RETURNING id
                """,
                (snapshot_date,),
            )
            snapshot_id = cur.fetchone()[0]
            self.conn.commit()
            return snapshot_id

    def ensure_not_exists(self, snapshot_date):
        """
        Hard guard against duplicates (your rule)
        """
        existing = self.get_by_date(snapshot_date)
        if existing:
            raise ValueError(f"Snapshot already exists for {snapshot_date}")

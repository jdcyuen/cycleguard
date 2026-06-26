from typing import Optional

import psycopg


class SnapshotRepositoryError(Exception):
    """Raised when snapshot repository operations fail."""


class SnapshotRepository:
    def __init__(
        self,
        conn,
    ):
        self.conn = conn

    def get_by_date(
        self,
        snapshot_date,
    ) -> Optional[int]:
        """
        Returns snapshot_id if exists, else None
        """

        try:
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

        except psycopg.Error as exc:
            raise SnapshotRepositoryError(
                f"Failed to lookup snapshot "
                f"for date={snapshot_date}"
            ) from exc

    def create(
        self,
        snapshot_date,
    ) -> int:
        """
        Creates snapshot and returns snapshot_id
        """

        try:
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

        except psycopg.IntegrityError as exc:
            self.conn.rollback()

            raise SnapshotRepositoryError(
                f"Snapshot already exists "
                f"for date={snapshot_date}"
            ) from exc

        except psycopg.Error as exc:
            self.conn.rollback()

            raise SnapshotRepositoryError(
                f"Failed to create snapshot "
                f"for date={snapshot_date}"
            ) from exc

    def ensure_not_exists(
        self,
        snapshot_date,
    ):
        """
        Hard guard against duplicates.
        """

        existing = self.get_by_date(
            snapshot_date
        )

        if existing:
            raise ValueError(
                f"Snapshot already exists "
                f"for {snapshot_date}"
            )
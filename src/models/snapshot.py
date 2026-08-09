from dataclasses import dataclass
from datetime import date
from datetime import datetime
from typing import Optional


@dataclass(slots=True)
class Snapshot:
    """
    Represents a single holdings snapshot for
    one account on one trading day.
    """

    id: Optional[int] = None

    account_id: int = 0

    snapshot_date: Optional[date] = None

    created_at: Optional[datetime] = None

    import_history_id: int = None
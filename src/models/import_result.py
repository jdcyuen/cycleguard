from dataclasses import dataclass, field
from datetime import date

@dataclass(frozen=True)
class ImportResult:
    """
    Result returned by an ingestion service.
    """

    account_id: int
    account_name: str
    institution: str

    import_type: str
    filename: str

    snapshot_date: date | None

    rows_read: int = 0
    rows_imported: int = 0
    rows_skipped: int = 0

    snapshot_id: int | None = None
    import_history_id: int | None = None

    elapsed_ms: int = 0

    status: str = "SUCCESS"

    warnings: list[str] = field(default_factory=list)

    dry_run: bool = False

    
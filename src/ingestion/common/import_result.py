from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ImportResult:
    """
    Result returned by an ingestion service.
    """

    account_name: str
    import_type: str   
    file_name: str

    rows_processed: int = 0
    rows_imported: int = 0
    rows_failed: int = 0

    snapshot_id: Optional[int] = None

    errors: List[str] = field(
        default_factory=list
    )

    status: str = "SUCCESS"

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional



@dataclass(slots=True)
class ImportHistory:

    """
    Records every positions or transactions import.
    Serves as an audit trail for the ingestion pipeline.
    """

    id: Optional[int] = None
    account_id: int = None

    # "positions" or "transactions"
    import_type: str = None

    institution: str = ""
    # Fidelity, Schwab, Vanguard, etc.

    filename: str = None

    # SHA256 of the imported file
    file_hash: str = None

    # Only used for positions imports
    snapshot_date: Optional[date] = None

    import_timestamp: Optional[datetime] = None

    rows_read: int = 0

    rows_imported: int = 0

    rows_skipped: int = 0

    # SUCCESS / PARTIAL / FAILED
    status: str = "SUCCESS"

    elapsed_ms: int = 0

    error_message: Optional[str] = None
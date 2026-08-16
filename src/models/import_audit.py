from dataclasses import dataclass
from enum import Enum


class ImportAuditStatus(Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"


@dataclass(slots=True)
class ImportAuditResult:
    import_id: int
    status: ImportAuditStatus
    message: str
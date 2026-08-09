from dataclasses import dataclass
from typing import Optional

@dataclass(slots=True)
class Security:
    """
    Security entity.
    """

    id: Optional[int] = None
    symbol: str = ""
    description: Optional[str] = None
    asset_type: Optional[str] = None
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

    # Describe what kind of security an instrument is: e.g. "ETF", "Common Stock", "Mutual Fund", "CD", "Savings Account"
    asset_type: Optional[str] = None
    
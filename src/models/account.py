from dataclasses import dataclass
from typing import Optional

@dataclass(slots=True)
class Account:
    """
    Account entity.
    """

    id:  Optional[int] = None
    account_number: str = ""
    name: str = ""
    institution: str = ""
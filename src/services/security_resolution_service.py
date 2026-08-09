# src/services/security_resolution_service.py

from dataclasses import asdict

from models.security import Security

import yfinance as yf

from core.logger import get_logger

logger = get_logger(__name__)


class SecurityResolutionService:
    """
    Resolves symbols to security IDs.

    Creates a new security if one does not exist.
    """

    def __init__(
        self,
        security_repo,
    ):
        self._security_repo = security_repo


    def get_quote_type(self,symbol: str) -> str | None:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            return info.get("quoteType")

        except Exception:
            return None

    @staticmethod
    def get_missing_fields(security: Security) -> list[str]:
        return [
            field
            for field, value in asdict(security).items()
            if value is None
            or (isinstance(value, str) and value.strip() == "")
        ]


    def resolve(
        self,
        security: Security,
    ) -> Security:

        logger.debug(
            "Resolving security: %s",
            security.symbol
        )

        # Normalize special Fidelity symbol
        if security.symbol == "FDRXX":
            security = Security(
                symbol="FDRXX",
                description="Fidelity Government Cash Reserves",
            )
        
        security.asset_type = self.get_quote_type(security.symbol)

        logger.info(
            "Creating or resolving security: %s",
            security
        )
        logger.info("upserting security: %s", security)

        return self._security_repo.upsert(security)
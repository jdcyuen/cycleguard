
import csv
from decimal import Decimal

from engine.trade_logger import CSVTradeLogger
from models.trade import Trade


def test_csv_trade_logger_logs_trade_objects(tmp_path):
    log_file = tmp_path / "trades.csv"

    logger = CSVTradeLogger(str(log_file))

    trades = [
        Trade(
            symbol="SGOV",
            action="SELL",
            amount=Decimal("100.00"),
        ),
        Trade(
            symbol="FZROX",
            action="BUY",
            amount=Decimal("50.00"),
        ),
    ]

    logger.log_trades(
        trades,
        "Level 1",
    )

    assert log_file.exists()

    content = log_file.read_text()

    assert "SGOV" in content
    assert "SELL" in content
    assert "100.00" in content

    assert "FZROX" in content
    assert "BUY" in content
    assert "50.00" in content
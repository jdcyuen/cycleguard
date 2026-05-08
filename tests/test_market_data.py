import unittest
from unittest.mock import patch
from src.data.market_data import get_market_data


class TestMarketData(unittest.TestCase):
    @patch("src.data.market_data.ConfigLoader")
    @patch("src.data.market_data.CrashManager")
    def test_get_market_data(self, mock_manager, mock_loader):

        # Mock config loader
        mock_loader.return_value.load.return_value = {}

        # Mock CrashManager output
        mock_instance = mock_manager.return_value
        mock_instance.run.return_value = {
            "close": 5000.0,
            "cycle_peak": 5200.0,
            "drawdown": -0.038,
            "signal": None,
        }

        data = get_market_data()

        self.assertEqual(data["close"], 5000.0)
        self.assertEqual(data["drawdown"], -0.038)
        self.assertEqual(data["cycle_peak"], 5200.0)


if __name__ == "__main__":
    unittest.main()

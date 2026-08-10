import unittest
from unittest.mock import patch
from data.market_data import get_market_data


class TestMarketData(unittest.TestCase):
    @patch("data.market_data.get_config")
    @patch("data.market_data.CrashManager")
    def test_get_market_data(self, mock_manager, mock_get_config):

        # Mock config
        mock_get_config.return_value = {}

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

        mock_get_config.assert_called_once()
        mock_manager.assert_called_once_with({})
        mock_instance.run.assert_called_once()


if __name__ == "__main__":
    unittest.main()

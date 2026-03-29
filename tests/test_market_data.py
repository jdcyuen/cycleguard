import unittest
import pandas as pd
from unittest.mock import patch
from src.utils.market_data import MarketData


class TestMarketData(unittest.TestCase):
    def setUp(self):
        # Provide a mock config
        self.mock_config = {
            "market": {
                "ticker": "^GSPC",
                "start_date": "2015-01-01",
                "recovery_threshold": 0.95,
            }
        }
        self.md = MarketData(self.mock_config)

    @patch("src.utils.market_data.yf.download")
    def test_fetch(self, mock_download):
        # Mock the yfinance dataframe response
        mock_df = pd.DataFrame(
            {"Close": [100.0, 105.0, 95.0]},
            index=pd.date_range(start="2020-01-01", periods=3),
        )
        mock_download.return_value = mock_df

        df = self.md.fetch()
        
        # Verify the dataframe structure matched Expectations
        self.assertEqual(list(df.columns), ["close"])
        self.assertEqual(len(df), 3)
        self.assertEqual(df["close"].iloc[0], 100.0)

    def test_detect_cycle_peak(self):
        # Create a sample dataframe
        # recovery threshold is 0.95.
        df = pd.DataFrame({
            "close": [100.0, 110.0, 80.0, 90.0, 105.0]  # Note: 105 >= 0.95 * 110 (104.5)
        })

        df = self.md.detect_cycle_peak(df)
        
        expected_peaks = [
            100.0,  # Starts at 100
            110.0,  # New high 110 > 100
            110.0,  # 80 is not high, and not >= 0.95 * 110
            110.0,  # 90 is not high, and not >= 0.95 * 110
            105.0   # 105 is not high (105 < 110), but 105 >= 0.95 * 110 (104.5), so peak resets to 105
        ]
        
        self.assertListEqual(df["cycle_peak"].tolist(), expected_peaks)

    def test_calculate_drawdown(self):
        df = pd.DataFrame({
            "close": [100.0, 80.0],
            "cycle_peak": [100.0, 100.0]
        })
        
        df = self.md.calculate_drawdown(df)
        
        expected_drawdowns = [
            0.0,    # (100 - 100) / 100
            -0.20   # (80 - 100) / 100
        ]
        
        self.assertAlmostEqual(df["drawdown"].iloc[0], expected_drawdowns[0])
        self.assertAlmostEqual(df["drawdown"].iloc[1], expected_drawdowns[1])

    @patch("src.utils.market_data.MarketData.fetch")
    def test_latest(self, mock_fetch):
        # Mock the fetch method to return a controlled dataframe
        mock_fetch.return_value = pd.DataFrame({
            "close": [100.0, 110.0, 80.0]
        })
        
        latest_data = self.md.latest()
        
        self.assertEqual(latest_data["price"], 80.0)
        self.assertEqual(latest_data["cycle_peak"], 110.0)
        self.assertAlmostEqual(latest_data["drawdown"], -30.0 / 110.0)

    @patch("src.utils.market_data.MarketData.fetch")
    def test_run(self, mock_fetch):
        mock_fetch.return_value = pd.DataFrame({
            "close": [100.0, 110.0, 80.0]
        })
        
        df = self.md.run()
        
        self.assertIn("close", df.columns)
        self.assertIn("cycle_peak", df.columns)
        self.assertIn("drawdown", df.columns)
        self.assertEqual(len(df), 3)


if __name__ == "__main__":
    unittest.main()

import unittest
import pandas as pd
from unittest.mock import MagicMock
from src.engine.crash_manager import CrashManager, IMarketDataProvider


class TestCrashManager(unittest.TestCase):
    def setUp(self):
        # Mock Config
        self.mock_config = {
            "market": {
                "ticker": "^GSPC",
                "start_date": "2015-01-01",
                "recovery_threshold": 0.95,
            },
            "deployment": {
                "levels": {
                    "Level 1": 0.03,
                    "Level 2": 0.05,
                    "Level 3": 0.08,
                    "Level 4": 0.09
                }
            }
        }
        
        # Inject a mock data provider to comply with DIP
        self.mock_provider = MagicMock(spec=IMarketDataProvider)
        self.cm = CrashManager(self.mock_config, data_provider=self.mock_provider)

    def test_detect_cycle_peak(self):
        # Setup data: 120, 100, 115
        # peak should be 120, 120, 115 (since 115 > 0.95 * 120 = 114)
        df = pd.DataFrame({"close": [120.0, 100.0, 115.0]})
        df = self.cm.detect_cycle_peak(df)
        
        self.assertEqual(df["cycle_peak"].iloc[0], 120.0)
        self.assertEqual(df["cycle_peak"].iloc[1], 120.0)
        self.assertEqual(df["cycle_peak"].iloc[2], 115.0)

    def test_run_orchestrates_provider(self):
        """Verifies that the engine orchestrates data fetching through the injected provider."""
        # Setup mock return value
        mock_df = pd.DataFrame({"close": [100.0, 50.0]})
        self.mock_provider.fetch_data.return_value = mock_df
        
        # Execute
        result = self.cm.run()

        # Verify the Dependency was utilized correctly (DIP/SRP check)
        self.mock_provider.fetch_data.assert_called_once_with("^GSPC", "2015-01-01")
        
        # Verify calculation logic (50 is -50% from 100, so Level 4)
        self.assertEqual(result["price"], 50.0)
        self.assertEqual(result["drawdown"], -0.5)
        self.assertEqual(result["signal"], "Level 4")

    def test_no_crash_below_level1(self):
        # Drawdowns below 10% should return None
        # Using the standard thresholds from the class (not the mock config's values which were different for testing)
        self.assertEqual(self.cm.get_signal(-0.05), None)
        self.assertEqual(self.cm.get_signal(0.0), None)

    def test_level1_detection(self):
        self.assertEqual(self.cm.get_signal(-0.15), "Level 1")


if __name__ == "__main__":
    unittest.main()

# test_crash_manager.py

import unittest
from src.engine.crash_manager import CrashManager


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
        self.cm = CrashManager(self.mock_config)

    def test_no_crash_below_level1(self):
        # Drawdowns below 10% (e.g., drops of 3%, 0%) should return None
        self.assertIsNone(self.cm.get_signal(-0.03))
        self.assertIsNone(self.cm.get_signal(0.00))

    def test_level1_crash(self):
        # Drawdown below -10% but above -20% triggers Level 1
        self.assertEqual(self.cm.get_signal(-0.11), "Level 1")
        self.assertEqual(self.cm.get_signal(-0.15), "Level 1")

    def test_level2_crash(self):
        # Drawdown below -20% but above -30% triggers Level 2
        self.assertEqual(self.cm.get_signal(-0.21), "Level 2")
        self.assertEqual(self.cm.get_signal(-0.25), "Level 2")

    def test_level3_crash(self):
        # Drawdown below -30% but above -40% triggers Level 3
        self.assertEqual(self.cm.get_signal(-0.31), "Level 3")
        self.assertEqual(self.cm.get_signal(-0.35), "Level 3")

    def test_level4_crash(self):
        # Drawdown below -40% triggers Level 4
        self.assertEqual(self.cm.get_signal(-0.41), "Level 4")
        self.assertEqual(self.cm.get_signal(-0.50), "Level 4")

    def test_exact_boundary(self):
        # Test exact boundaries of crash levels
        self.assertEqual(self.cm.get_signal(-0.10), "Level 1")
        self.assertEqual(self.cm.get_signal(-0.20), "Level 2")
        self.assertEqual(self.cm.get_signal(-0.30), "Level 3")
        self.assertEqual(self.cm.get_signal(-0.40), "Level 4")


if __name__ == "__main__":
    unittest.main()

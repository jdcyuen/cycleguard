import unittest
import io
from src.dashboard.components.sync_fidelity import parse_fidelity_csv


class TestFidelitySync(unittest.TestCase):
    def test_parse_clean_csv(self):
        csv_content = """Symbol,Current Value
AAPL,150.0
GOOG,2800.0
"""
        file = io.BytesIO(csv_content.encode("utf-8"))
        portfolio = parse_fidelity_csv(file)
        
        self.assertIsNotNone(portfolio)
        self.assertEqual(portfolio["AAPL"], 150.0)
        self.assertEqual(portfolio["GOOG"], 2800.0)

    def test_parse_csv_with_metadata_header(self):
        csv_content = """Account: 123456
Date: 2026-03-31
Symbol,Current Value
AAPL,150.0
GOOG,2800.0
"""
        file = io.BytesIO(csv_content.encode("utf-8"))
        portfolio = parse_fidelity_csv(file)
        
        self.assertIsNotNone(portfolio)
        self.assertEqual(portfolio["AAPL"], 150.0)
        self.assertEqual(portfolio["GOOG"], 2800.0)

    def test_parse_csv_with_trailing_garbage(self):
        csv_content = """Symbol,Current Value
AAPL,150.0
GOOG,2800.0
Total Portfolio Value: 2950.0
"""
        file = io.BytesIO(csv_content.encode("utf-8"))
        portfolio = parse_fidelity_csv(file)
        
        # Should still parse the valid rows
        self.assertIsNotNone(portfolio)
        self.assertEqual(portfolio["AAPL"], 150.0)
        self.assertEqual(portfolio["GOOG"], 2800.0)

    def test_parse_csv_with_duplicate_symbols(self):
        csv_content = """Symbol,Current Value
AAPL,100.0
AAPL,50.0
GOOG,2800.0
"""
        file = io.BytesIO(csv_content.encode("utf-8"))
        portfolio = parse_fidelity_csv(file)
        
        # Should sum duplicates (100 + 50 = 150)
        self.assertIsNotNone(portfolio)
        self.assertEqual(portfolio["AAPL"], 150.0)

    def test_invalid_csv_no_headers(self):
        csv_content = """Ticker,Price
AAPL,150.0
"""
        file = io.BytesIO(csv_content.encode("utf-8"))
        # We need to mock st.error for the component test
        import streamlit as st
        from unittest.mock import patch
        
        with patch("streamlit.error") as mock_error:
            portfolio = parse_fidelity_csv(file)
            self.assertIsNone(portfolio)
            mock_error.assert_called_with("No valid 'Symbol' and 'Current Value' headers found in CSV.")


if __name__ == "__main__":
    unittest.main()

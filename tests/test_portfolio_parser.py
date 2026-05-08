import unittest
import io
from src.engine.portfolio_parser import FidelityParser


class TestPortfolioParser(unittest.TestCase):
    def setUp(self):
        self.parser = FidelityParser()

    def test_fidelity_parsing_with_metadata(self):
        """Verifies that the parser finds the header regardless of leading metadata."""
        csv_content = """
Account Number,Account Name,Symbol,Description,Quantity,Last Price,Unused,Current Value
12345,IRA,AAPL,APPLE INC,10,123.45,," $1,234.56 "
12345,IRA,MSFT,MICROSOFT,5,200.00,,"1,000"
"""
        # Simulate a file object (Streamlit style)
        file = io.StringIO(csv_content.strip())
        result = self.parser.parse(file)

        self.assertIsNotNone(result)
        self.assertEqual(result["AAPL"], 1234.56)
        self.assertEqual(result["MSFT"], 1000.0)
        self.assertEqual(len(result), 2)

    def test_currency_cleaning(self):
        """Verifies that $, commas, and whitespace are handled correctly."""
        csv_content = """
Account Number,Account Name,Symbol,Description,Quantity,Last Price,Unused,Current Value
12345,IRA,AAPL,APPLE INC,10,123.45,," $1,234.56 "
12345,IRA,MSFT,MICROSOFT,5,200.00,,"1,000"
"""
        file = io.StringIO(csv_content.strip())
        result = self.parser.parse(file)

        self.assertEqual(result["AAPL"], 1234.56)
        self.assertEqual(result["MSFT"], 1000.0)

    def test_invalid_csv_returns_none(self):
        """Verifies that a junk file returns None instead of crashing."""
        csv_content = "This is not a CSV file with symbols."
        file = io.StringIO(csv_content)
        result = self.parser.parse(file)
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()

import unittest
import io
from src.engine.portfolio_parser import FidelityParser

class TestFidelitySync(unittest.TestCase):
    def setUp(self):
        self.parser = FidelityParser()

    def test_robust_parsing_with_metadata(self):
        # A semi-realistic Fidelity CSV snippet
        csv_content = """
Brokerage: Fidelity
Account: 12345
,,
Symbol,Description,Current Value
SMH,VANECK SEMI,"$10,500.25"
SCHG,SCHWAB GROWTH,"$5,000.00"
,,
Total Value,,$15,500.25
"""
        file = io.StringIO(csv_contents.strip() if hasattr(self, 'csv_contents') else csv_content.strip())
        portfolio = self.parser.parse(file)
        
        self.assertIsNotNone(portfolio)
        self.assertEqual(portfolio["SMH"], 10500.25)
        self.assertEqual(portfolio["SCHG"], 5000.00)

    def test_missing_headers_returns_none(self):
        csv_content = "This is a random file without Symbol headers."
        file = io.StringIO(csv_content)
        portfolio = self.parser.parse(file)
        self.assertIsNone(portfolio)

if __name__ == "__main__":
    unittest.main()

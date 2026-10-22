import yfinance as yf

# Define the stock ticker symbol (e.g., Apple Inc.)
ticker_symbol = "fzrox"

# Download historical data (default is daily)
df = yf.download(ticker_symbol, start="2020-01-01", end="2024-12-31")

# Display the first few rows
print(df.head())

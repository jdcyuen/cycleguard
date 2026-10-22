# src/stock_dashboard.py
import streamlit as st
import yfinance as yf
import pandas as pd
from typing import List, Dict
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
from datetime import datetime, timedelta


# -----------------------------
# Single Responsibility: StockFetcher
# -----------------------------


class StockFetcher:
    def __init__(self, tickers: list):
        self.tickers = tickers

    # ---------------------------
    # Private helper: YTD & 1-Year performance
    # ---------------------------
    def _get_performance(self, ticker):
        try:
            today = datetime.today()

            # YTD
            ytd_start = datetime(today.year, 1, 1)
            ytd_data = yf.download(ticker, start=ytd_start, end=today + timedelta(days=1),
                                   auto_adjust=True, progress=False)
            if ytd_data.empty:
                return None, None

            ytd_start_price = float(ytd_data["Close"].iloc[0])
            latest_price = float(ytd_data["Close"].iloc[-1])
            ytd_perf = ((latest_price - ytd_start_price) / ytd_start_price) * 100

            print(f"[DEBUG] {ticker} YTD Start Price: {ytd_start_price}")
            print(f"[DEBUG] {ticker} Latest Price: {latest_price}")
            print(f"[DEBUG] {ticker} YTD Performance (raw): {ytd_perf}")

            # 1-Year
            one_year_ago = today - timedelta(days=365)
            one_year_data = yf.download(ticker, start=one_year_ago, end=today + timedelta(days=1),
                                        auto_adjust=True, progress=False)
            if one_year_data.empty:
                return round(ytd_perf, 2), None

            one_year_start_price = float(one_year_data["Close"].iloc[0])
            one_year_perf = ((latest_price - one_year_start_price) / one_year_start_price) * 100

            print(f"[DEBUG] {ticker} 1Y Start Price: {one_year_start_price}")
            print(f"[DEBUG] {ticker} 1Y Performance (raw): {one_year_perf}")

            return round(ytd_perf, 2), round(one_year_perf, 2)

        except Exception as e:
            st.error(f"Error fetching performance for {ticker}: {e}")
            return None, None

    # ---------------------------
    # Public method: fetch stock data
    # ---------------------------
    def fetch_data(self) -> pd.DataFrame:
        rows = []
        for ticker in self.tickers:
            try:
                stock = yf.Ticker(ticker)
                info = stock.info

                current_price = info.get("regularMarketPrice", 0)
                change = info.get("regularMarketChange", 0)
                pct_change = info.get("regularMarketChangePercent", 0)
                market_cap = info.get("marketCap", 0)
                volume = info.get("volume", 0)
                avg_volume = info.get("averageVolume", 0)
                fifty_two_week = f"{info.get('fiftyTwoWeekLow', 0):,.2f} / {info.get('fiftyTwoWeekHigh', 0):,.2f}"

                # YTD and 1-Year performance
                ytd_perf, one_year_perf = self._get_performance(ticker)

                row = {
                    "Name": info.get("shortName", ""),
                    "Ticker": ticker.upper(),
                    "Exchange": info.get("exchange", ""),
                    "Sector": info.get("sector", ""),
                    "Industry": info.get("industry", ""),
                    "Current Price": current_price,
                    "52W Low/High": fifty_two_week,
                    "% Change": round(pct_change, 2) if pct_change is not None else 0.0,
                    "$ Change": round(change, 2) if change is not None else 0.0,
                    "YTD Performance (%)": ytd_perf,
                    "1-Year Performance (%)": one_year_perf,
                    "Market Cap": market_cap,
                    "Volume": volume,
                    "Avg Volume": avg_volume
                }
                rows.append(row)

            except Exception as e:
                st.error(f"Error fetching data for {ticker}: {e}")

        df = pd.DataFrame(rows)

        # Ensure YTD and 1-Year columns exist
        for col_name in ["YTD Performance (%)", "1-Year Performance (%)"]:
            if col_name not in df.columns:
                df[col_name] = 0.0

        # Safe column reordering: insert YTD and 1-Year performance after $ Change
        cols = df.columns.tolist()
        for col_name in ["YTD Performance (%)", "1-Year Performance (%)"]:
            if col_name in cols:
                cols.remove(col_name)

        if "$ Change" in cols:
            insert_idx = cols.index("$ Change") + 1
        elif "% Change" in cols:
            insert_idx = cols.index("% Change") + 1
        else:
            insert_idx = len(cols)

        cols[insert_idx:insert_idx] = ["YTD Performance (%)", "1-Year Performance (%)"]
        df = df[cols]

        return df





# -----------------------------
# Single Responsibility: TableRenderer
# -----------------------------
class TableRenderer:
    def __init__(self, df):
        self.df = df

    def render(self):
        gb = GridOptionsBuilder.from_dataframe(self.df)
        gb.configure_default_column(editable=False, groupable=True, resizable=True)

        # Build initial grid options
        grid_options = gb.build()

        # Pin "Name" and "Ticker" columns and set widths
        for col in grid_options["columnDefs"]:
            if col["field"] == "Name":
                col["pinned"] = "left"
                col["width"] = 200
            elif col["field"] == "Ticker":
                col["pinned"] = "left"
                col["width"] = 100
            else:
                col["autoHeight"] = False
                col["minWidth"] = 100

        # Conditional formatting JS for numeric columns
        color_code = JsCode("""
        function(params) {
            if (params.value > 0) {
                return {'color': 'green', 'fontWeight': 'bold'};
            } else if (params.value < 0) {
                return {'color': 'red', 'fontWeight': 'bold'};
            }
            return {};
        }
        """)

        # Tooltip JS: show value with 2 decimal points
        tooltip_code = JsCode("""
        function(params) {
            return params.value != null ? params.value.toFixed(2) : '';
        }
        """)

        # Apply formatting to multiple numeric columns
        numeric_columns = ["% Change", "$ Change", "YTD Performance (%)", "1-Year Performance (%)"]
        for col_name in numeric_columns:
            for col in grid_options["columnDefs"]:
                if col["field"] == col_name:
                    col["cellStyle"] = color_code
                    col["tooltipValueGetter"] = tooltip_code

        # Dynamic table height: 35 px per row + 50 px header, max 600px
        table_height = min(600, 35 * len(self.df) + 50)

        AgGrid(
            self.df,
            gridOptions=grid_options,
            fit_columns_on_grid_load=True,
            height=table_height,
            allow_unsafe_jscode=True
        )







# -----------------------------
# Dependency Inversion / Main
# -----------------------------
def main():
    st.set_page_config(page_title="Stock Financial Dashboard", layout="wide")
    st.title("📈 Stock Financial Dashboard")

    # Sidebar input
    tickers_input = st.sidebar.text_input(
        "Enter stock tickers (comma separated)", "AAPL,MSFT,GOOGL"
    )
    tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]

    if tickers:
        fetcher = StockFetcher(tickers)
        df = fetcher.fetch_data()
        if not df.empty:
            table = TableRenderer(df)
            table.render()
        else:
            st.warning("No data available for the given tickers.")


# -----------------------------
# Entry point
# -----------------------------
if __name__ == "__main__":
    main()




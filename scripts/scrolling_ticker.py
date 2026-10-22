# scrolling_ticker_sidebar.py 
import streamlit as st 
import yfinance as yf 
import pandas as pd 
from abc import ABC, abstractmethod 
from streamlit_autorefresh import st_autorefresh
import asyncio
import sys

# Fix event loop issue on Windows
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


# ========================= 
# Abstract Interfaces 
# ========================= 
class MarketDataFetcher(ABC): 
    @abstractmethod 
    def get_data(self) -> pd.DataFrame: 
	    pass 
		
class Formatter(ABC): 
    @abstractmethod 
    def format(self, df: pd.DataFrame) -> str: 
	    pass 
		
class Renderer(ABC): 
    @abstractmethod 
    def render(self, content: str) -> None: 
	    pass 

# ========================= 
# Concrete Implementations 
# ========================= 

class YahooFinanceFetcher(MarketDataFetcher): 
    """Fetches market data including Treasury 32nds""" 
    def __init__(self, tickers: dict): 
        self.tickers = tickers 
		
    def get_data(self) -> pd.DataFrame: 
        data = {} 
        for name, ticker in self.tickers.items(): 
            if ticker == "^TNX": 
                price = 100.00 
                change_32 = -2 
                change_pct = -0.0625 
                change_display = f"{change_32}/32 ({change_pct:+.2f}%)" 
                data[name] = {"Price": price, "ChangeDisplay": change_display} 
            else: 
                try: 
                    info = yf.Ticker(ticker).info 
                    last = info.get("regularMarketPrice", None) 
                    change = info.get("regularMarketChangePercent", None) 
                    change_display = f"{change:+.2f}%" if change is not None else "N/A" 
                    data[name] = {"Price": last, "ChangeDisplay": change_display}
                except Exception: 
                    data[name] = {"Price": None, "ChangeDisplay": "N/A"}
					
        return pd.DataFrame(data).T 

class TickerFormatter(Formatter): 
    """Formats DataFrame into HTML ticker bar""" 
    def format(self, df: pd.DataFrame) -> str: 
        items = [] 
        for idx, row in df.iterrows(): 
            change_str = row["ChangeDisplay"] 
		
		    # Determine color 
            if "(" in change_str: 
                pct_part = change_str.split("(")[1].replace("%)","") 
                color = "#00C853" if float(pct_part) >= 0 else "#D50000" 
            elif change_str == "N/A": 
                color = "white" 
            else: 
                try: 
                    pct_val = float(change_str.replace("%", "")) 
                    color = "#00C853" if pct_val >= 0 else "#D50000" 
                except Exception: 
                    color = "white" 
				
            price = row['Price'] 
            price_str = f"{price:.2f}" if price is not None else "N/A" 
		
            items.append( 
		        f"<span style='margin-right:40px'>{idx}: {price_str} " 
			    f"<span style='color:{color}'>{change_str}</span></span>" 
		    ) 
        ticker_html = " ".join(items) 
        html = f"""
                <div style="
                    max-width:100vw;     /* The container can expand up to 99% of the page width. */
                    margin:5px auto;   /* vertical margin (top & bottom) → adds a small gap above and below the ticker, auto horizontal margin → centers the container horizontally within its parent*/
                    border-radius:12px; /* optional rounded edges */
                    overflow:hidden;    /* Anything overflowing outside the box won’t show. Important here because the text scrolls across — prevents it from sticking outside the container.*/
                    white-space:nowrap; /* Prevents the ticker items from breaking into multiple lines. Ensures all symbols scroll in a single continuous row. */
                    background-color:#1E2A38; /* Dark navy background color. Makes the ticker look like a banner across the page*/
                    color:white;        /* */
                    padding:10px 0;     /* Adds 10px padding on top and bottom, 0px on left and right. Makes the ticker taller and text less cramped.*/
                    font-size:18px;     /* */
                    font-weight:bold;   /* */
                    box-shadow:0 2px 6px rgba(0,0,0,0.4); /* optional shadow */
                ">
                    <div style="
                        display:inline-block;
                        padding-left:5%;
                        animation:scroll-left 100s linear infinite; /* Control scroll speed */
                    ">
                        <span style="margin-right:500px">{ticker_html}</span>
                        <span style="margin-right:500px">{ticker_html}</span>
                        <span style="margin-right:500px">{ticker_html}</span>
                        <span style="margin-right:500px">{ticker_html}</span>
                        <span style="margin-right:500px">{ticker_html}</span>
                        <span style="margin-right:500px">{ticker_html}</span>
                        <span style="margin-right:500px">{ticker_html}</span>
                    </div>
                </div>

                <style>
                    @keyframes scroll-left {{
                        0%   {{ transform: translateX(0%); }}
                        100% {{ transform: translateX(-50%); }}
                    }}
                </style>
            """
        return html
 

class StreamlitRenderer(Renderer):
		
    """Renders formatted content in Streamlit""" 
    def render(self, content: str) -> None: 
	    st.markdown(content, unsafe_allow_html=True) 

# ========================= 
# Dashboard 
# ========================= 

class MarketDashboard: 
    def __init__(self, fetcher: MarketDataFetcher, formatter: Formatter, renderer: Renderer): 
        self.fetcher = fetcher
        self.formatter = formatter
        self.renderer = renderer
		
    def run(self): 
        df = self.fetcher.get_data() 
        content = self.formatter.format(df) 
        self.renderer.render(content) 

# ========================= 
# Streamlit App 
# ========================= 
def main():
    st.set_page_config(page_title="Market Dashboard", layout="wide")

    # Sidebar
    st.sidebar.title("Market Dashboard Settings")
    auto_refresh = st.sidebar.slider("Auto-refresh interval (seconds)", 5, 60, 10)
        
    # Example tickers input (can also use fixed margins version)
    default_tickers_text = """Dow Jones:^DJI
    S&P 500:^GSPC
    Nasdaq:^IXIC
    Russell 2000:^RUT
    US 10Y:^TNX
    VIX:^VIX
    Gold:GC=F
    Crude Oil:CL=F
    Bitcoin:BTC-USD
    KBW Bank:^BKX
    S&P GSCI:^SPGSCI
    Dollar Index:^NYICDX"""

    tickers_input = st.sidebar.text_area(
            "Market indices (Name:Ticker, one per line)", 
            value=default_tickers_text,
            height=250
        )

    tickers = {}
    for line in tickers_input.strip().split("\n"):
        if ":" in line:
            name, ticker = line.split(":", 1)
            tickers[name.strip()] = ticker.strip()

   # Initialize dashboard
    fetcher = YahooFinanceFetcher(tickers)
    formatter = TickerFormatter()
    renderer = StreamlitRenderer()
    dashboard = MarketDashboard(fetcher, formatter, renderer)

    # Auto-refresh
    st_autorefresh(interval=auto_refresh*1000, key="ticker_autorefresh")

    # Display scrolling ticker
    dashboard.run()

# Make sure this is **after** main() is defined
if __name__ == "__main__":
    main()

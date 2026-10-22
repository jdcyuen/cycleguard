import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# --- Page config ---
st.set_page_config(page_title="Performance Comparison", layout="wide")
st.title("📊 Interactive Performance Comparison: Stocks, ETFs, Mutual Funds vs S&P 500 & DJIA")

# --- Sidebar options ---
st.sidebar.header("Settings")

# Checkboxes for benchmarks
show_sp500 = st.sidebar.checkbox("Show S&P 500", value=True)
show_djia = st.sidebar.checkbox("Show DJIA", value=True)
show_nasdaq = st.sidebar.checkbox("Show Nasdaq (IXIC)", value=True)

# Text input for any tickers (comma-separated)
ticker_input = st.sidebar.text_area(
    "Enter tickers to compare (comma-separated, e.g., AAPL,VTI,FZROX):",
    value="AAPL,VTI,FZROX"
)

# Process user input into a list, remove empty entries, strip whitespace
user_tickers = [t.strip().upper() for t in ticker_input.split(",") if t.strip()]

# Benchmark selection
benchmark = st.sidebar.selectbox(
    "Select Benchmark",
    options=['S&P 500', 'DJIA', 'Nasdaq'],
    index=0
)

start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2023-01-01"))
end_date = st.sidebar.date_input("End Date", pd.to_datetime("today"))

log_scale = st.sidebar.checkbox("Use Logarithmic Scale", value=False)
line_width = st.sidebar.slider("Line Thickness", 0.5, 5.0, 1.5, 0.1)
marker_size = st.sidebar.slider("Marker Size", 1, 10, 4, 1)
fig_width = st.sidebar.slider("Graph Width (px)", 400, 2500, 1400, 50)
fig_height = int(fig_width * 0.6)

# --- Download data ---
@st.cache_data
def get_data(symbols, start, end):
    try:
        data = yf.download(symbols, start=start, end=end, auto_adjust=True)['Close']
        return data
    except Exception as e:
        st.error(f"Error downloading data: {e}")
        return pd.DataFrame()

if user_tickers:
    # Build list of tickers to download
    tickers_to_download = user_tickers.copy()

    # Always include benchmark for calculations
    if benchmark == 'S&P 500' and '^GSPC' not in tickers_to_download:
        tickers_to_download.append('^GSPC')
    elif benchmark == 'DJIA' and '^DJI' not in tickers_to_download:
        tickers_to_download.append('^DJI')

    # Always include both benchmarks to avoid KeyError
    if '^GSPC' not in tickers_to_download:
        tickers_to_download.append('^GSPC')
    if '^DJI' not in tickers_to_download:
        tickers_to_download.append('^DJI')
    if '^IXIC' not in tickers_to_download:
        tickers_to_download.append('^IXIC')
    

    data = get_data(tickers_to_download, start_date, end_date)

    if not data.empty:
        # Normalize to 100
        normalized = data / data.iloc[0] * 100

        # Determine benchmark ticker symbol
        if benchmark == 'S&P 500':
            benchmark_symbol = '^GSPC'
        elif benchmark == 'DJIA':
            benchmark_symbol = '^DJI'
        else:
            benchmark_symbol = '^IXIC'

        # Relative performance vs benchmark (avoid NaN)
        benchmark_series = normalized[benchmark_symbol].ffill().bfill()
        rel_perf = (normalized.div(benchmark_series, axis=0) * 100) - 100


        # Prepare long-form dataframe for plotting
        plot_df = normalized.reset_index().melt(id_vars='Date', var_name='Asset', value_name='Normalized Value')
        rel_df = rel_perf.reset_index().melt(
            id_vars='Date', var_name='Asset', value_name='Relative Performance (%)'
        )
        rel_df['Relative Performance (%)'] = rel_df['Relative Performance (%)'].fillna(0)

        plot_df = plot_df.merge(rel_df, on=['Date', 'Asset'])

        # Add asset ticker for hover
        plot_df['Ticker'] = plot_df['Asset']

        # Determine which assets to display based on checkboxes
        display_assets = []
        for asset in plot_df['Asset'].unique():
            if asset == '^GSPC' and not show_sp500:
                continue
            if asset == '^DJI' and not show_djia:
                continue
            if asset == '^IXIC' and not show_nasdaq:
                continue
            display_assets.append(asset)

        # Map benchmarks to nicer labels
        asset_labels = {
            "^GSPC": "S&P 500",
            "^DJI": "Dow Jones",
            "^IXIC": "Nasdaq"
        }

        # Create Plotly figure
        fig = go.Figure()

        for asset in display_assets:
            asset_df = plot_df[plot_df['Asset'] == asset]

            fig.add_trace(
                go.Scatter(
                    x=asset_df['Date'],
                    y=asset_df['Normalized Value'],
                    mode='lines+markers',
                    name=asset_labels.get(asset, asset),
                    line=dict(width=line_width),
                    marker=dict(size=marker_size),
                    customdata=asset_df['Relative Performance (%)'],  # just one column
                    hovertemplate=(
                        "%{fullData.name}<br>"
                        "Date: %{x|%Y-%m-%d}<br>"
                        "Normalized Value: %{y:.2f}<br>"
                        "Relative Performance: %{customdata:+.2f}%<extra></extra>"
                    )
                )
            )


        fig.update_layout(
            width=fig_width,
            height=fig_height,
            template='plotly_white',
            legend=dict(orientation='v', y=1, x=0, xanchor='left', yanchor='top'),
            title=f"Normalized Performance Comparison (Start=100) vs {benchmark}"
        )

        if log_scale:
            fig.update_yaxes(type='log')

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No data was returned. Check the ticker symbols or date range.")
else:
    st.info("Please enter at least one ticker to compare.")

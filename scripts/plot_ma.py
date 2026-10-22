import yfinance as yf
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from itertools import combinations

# ---- Page config ----
st.set_page_config(page_title="MA Crossovers", layout="wide")

# ---- App title ----
st.title("Interactive Stock Moving Averages, RSI & Crossovers")

# ---- Sidebar controls ----
st.sidebar.header("Settings")
ticker = st.sidebar.text_input("Ticker", "AAPL").upper()
start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2015-01-01"))

# Multiselect for moving averages
ma_options = list(range(5, 201))  # allow 5 to 200 days
selected_mas = st.sidebar.multiselect("Select Moving Averages (days)", ma_options, default=[50, 200])

# Plot size inputs
plot_height = st.sidebar.number_input("Plot Height", min_value=400, max_value=1200, value=600, step=50)
plot_width = st.sidebar.number_input("Plot Width", min_value=600, max_value=2000, value=1000, step=50)

# Toggles
show_volume = st.sidebar.checkbox("Show Volume", value=True)
show_rsi = st.sidebar.checkbox("Show RSI (Relative Strength Index)", value=False)

# Reset button
if st.sidebar.button("Reset Size"):
    plot_height, plot_width, show_volume, show_rsi = 600, 1000, True, False
    st.experimental_rerun()

# ---- Download data ----
data = yf.download(ticker, start=start_date, auto_adjust=False)

if data.empty:
    st.warning(f"No data found for {ticker}.")
else:
    # Flatten MultiIndex if necessary
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = [lvl0 for (lvl0, *_) in data.columns.values]

    if "Close" not in data.columns:
        st.error("No 'Close' column found in data.")
        st.stop()

    # Prepare data
    data["Close"] = pd.to_numeric(data["Close"], errors="coerce")
    if "Volume" in data.columns:
        data["Volume"] = pd.to_numeric(data["Volume"], errors="coerce")
    data = data.dropna(subset=["Close"])
    data.index = pd.to_datetime(data.index)

    # ---- Calculate moving averages ----
    for ma in selected_mas:
        data[f"SMA{ma}"] = data["Close"].rolling(window=ma).mean()

    # ---- Calculate RSI if enabled ----
    if show_rsi:
        delta = data["Close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data["RSI"] = 100 - (100 / (1 + rs))

    # ---- Build Plotly figure ----
    fig = go.Figure()

    # Price line
    fig.add_trace(go.Scatter(x=data.index, y=data["Close"], mode="lines", name="Close"))

    # MAs lines
    colors = ["red", "green", "orange", "purple", "brown", "pink", "cyan", "magenta"]
    for i, ma in enumerate(selected_mas):
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data[f"SMA{ma}"],
            mode="lines",
            name=f"SMA{ma}",
            line=dict(color=colors[i % len(colors)])
        ))

    # ---- Identify crossovers ----
    cross_events_list = []
    for short, long in combinations(selected_mas, 2):
        col_short, col_long = f"SMA{short}", f"SMA{long}"
        signal = (data[col_short] > data[col_long]).astype(int)
        cross = signal.diff()

        golden = data[cross == 1]
        death = data[cross == -1]

        # Add markers to plot
        fig.add_trace(go.Scatter(x=golden.index, y=golden[col_short],
                                 mode="markers",
                                 marker=dict(symbol="triangle-up", color="green", size=10),
                                 name=f"Golden {short}/{long}"))
        fig.add_trace(go.Scatter(x=death.index, y=death[col_short],
                                 mode="markers",
                                 marker=dict(symbol="triangle-down", color="red", size=10),
                                 name=f"Death {short}/{long}"))

        # Record cross events
        for df, typ in zip([golden, death], ["Golden Cross", "Death Cross"]):
            if not df.empty:
                df_events = pd.DataFrame({
                    "Date": df.index,
                    "Price": df[col_short],
                    "Type": f"{typ} {short}/{long}",
                    "Volume": df["Volume"] if "Volume" in df.columns else None
                }).reset_index(drop=True)
                cross_events_list.append(df_events)

    # ---- Volume ----
    if show_volume and "Volume" in data.columns:
        fig.add_trace(go.Bar(
            x=data.index,
            y=data["Volume"],
            name="Volume",
            marker_color="lightblue",
            yaxis="y2",
            opacity=0.5
        ))

    # Layout for price chart
    fig.update_layout(
        title=f"{ticker} Price with Moving Averages",
        xaxis_title="Date",
        yaxis_title="Price",
        yaxis2=dict(title="Volume", overlaying="y", side="right", showgrid=False),
        height=plot_height,
        width=plot_width,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    st.plotly_chart(fig)

    # ---- RSI chart ----
    if show_rsi and "RSI" in data.columns:
        fig_rsi = go.Figure()
        fig_rsi.add_trace(go.Scatter(x=data.index, y=data["RSI"], mode="lines", name="RSI", line=dict(color="blue")))
        fig_rsi.add_hline(y=70, line_dash="dash", line_color="red")
        fig_rsi.add_hline(y=30, line_dash="dash", line_color="green")

        fig_rsi.update_layout(
            title="Relative Strength Index (RSI)",
            xaxis_title="Date",
            yaxis_title="RSI",
            height=300,
            width=plot_width,
            yaxis=dict(range=[0, 100])
        )
        st.plotly_chart(fig_rsi)

    # ---- Cross Events Table ----
    if cross_events_list:
        cross_events = pd.concat(cross_events_list, ignore_index=True)
        cross_events["Date"] = pd.to_datetime(cross_events["Date"])
        cross_events = cross_events.sort_values("Date").reset_index(drop=True)
        st.subheader("Golden & Death Cross Events")
        st.dataframe(cross_events)
    else:
        st.info("No cross events found for the selected moving averages.")

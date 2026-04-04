# src/dashboard/components/portfolio_view.py

import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, ColumnsAutoSizeMode
import streamlit as st

def render_portfolio_view(portfolio):
    if not portfolio:
        st.info("No portfolio data available.")
        return

    # -------------------------
    # DATA PREP: Dictionary -> DataFrame
    # -------------------------
    total_value = sum(portfolio.values())
    
    data = []
    for ticker, value in portfolio.items():
        pct = (value / total_value) if total_value else 0
        data.append({
            "Symbol": ticker,
            "Current Value": value,
            "Percent of Account": pct
        })
    
    df = pd.DataFrame(data)
    
    # Sort by value descending by default
    df = df.sort_values("Current Value", ascending=False)

    # -------------------------
    # AG GRID CONFIG: The "WOW" Factor
    # -------------------------
    gb = GridOptionsBuilder.from_dataframe(df)
    
    # 1. Symbol Column (Frozen on the left)
    gb.configure_column(
        "Symbol", 
        header_name="Ticker", 
        pinned='left', 
        filter=True,
        cellStyle={'fontWeight': 'bold', 'color': '#00d4ff'}
    )
    
    # 2. Currency Formatting for Value
    gb.configure_column(
        "Current Value",
        header_name="Current Value ($)",
        type=["numericColumn", "numberColumnFilter"],
        valueFormatter="x.toLocaleString('en-US', {style: 'currency', currency: 'USD'})",
    )
    
    # 3. Percentage Formatting for Weight
    gb.configure_column(
        "Percent of Account",
        header_name="% of Account",
        type=["numericColumn"],
        valueFormatter="(x * 100).toFixed(2) + '%'",
    )
    
    # Build options
    grid_options = gb.build()
    
    # -------------------------
    # RENDER
    # -------------------------
    st.subheader("📊 Portfolio Overview")
    
    AgGrid(
        df,
        gridOptions=grid_options,
        # 'alpine' matches your premium dashboard visuals
        theme="alpine", 
        height=350,
        columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
        allow_unsafe_jscode=True # Crucial for the JavaScript value formatters
    )

    # Summary Stats below the grid
    st.caption(f"**Total Portfolio Value:** ${total_value:,.2f} | **Tickers Managed:** {len(portfolio)}")

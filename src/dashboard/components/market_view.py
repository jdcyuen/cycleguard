import streamlit as st

def render_market_view(market_df):
    st.subheader("📈 Market Data & Drawdowns")
    latest_market = market_df.iloc[-1]
    
    st.write(f"**Latest Market Price:** {latest_market['close']:.2f}")
    st.write(f"**Cycle Peak:** {latest_market['cycle_peak']:.2f}")
    st.write(f"**Current Drawdown:** {latest_market['drawdown']:.2%}")
    
    st.line_chart(market_df[["close", "cycle_peak"]])
    st.area_chart(market_df["drawdown"])

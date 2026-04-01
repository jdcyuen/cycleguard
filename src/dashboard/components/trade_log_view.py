import streamlit as st

def render_trade_log_view(trade_log_df):
    st.subheader("📋 Executed Trades")
    st.dataframe(trade_log_df.sort_values("date", ascending=False))

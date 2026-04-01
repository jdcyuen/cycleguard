import streamlit as st
import pandas as pd

def render_portfolio_view(portfolio):
    st.subheader("📊 Portfolio Overview")
    portfolio_df = pd.DataFrame(list(portfolio.items()), columns=["Ticker", "Value ($)"])
    portfolio_df["% of Portfolio"] = (
        portfolio_df["Value ($)"] / portfolio_df["Value ($)"].sum()
    )
    st.dataframe(
        portfolio_df.style.format({"Value ($)": "${:,.2f}", "% of Portfolio": "{:.2%}"})
    )
    st.write(f"**Total Portfolio Value:** ${portfolio_df['Value ($)'].sum():,.2f}")

import streamlit as st
import pandas as pd

def render_recovery_view(portfolio, market_snapshot, recovery_manager):
    st.subheader("🛠️ Recovery Management")
    portfolio_after_recovery = recovery_manager.trim_and_rebalance(
        portfolio, market_snapshot
    )
    st.dataframe(
        pd.DataFrame(
            list(portfolio_after_recovery.items()), columns=["Ticker", "Adjusted Value ($)"]
        )
    )

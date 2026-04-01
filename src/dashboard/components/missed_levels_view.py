import streamlit as st
from src.dashboard.utils import load_rebalance_state

def render_missed_levels_view():
    st.subheader("⚡ Missed Crash Levels")
    state = load_rebalance_state()
    executed_levels = state.get("executed_levels", [])
    
    if executed_levels:
        st.warning(
            "The following crash levels were triggered and executed (including catch-up from missed days):"
        )
        for level in executed_levels:
            st.write(f"• {level}")
    else:
        st.success("No crash levels have been triggered yet.")

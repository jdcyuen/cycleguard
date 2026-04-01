import streamlit as st

def render_signals_view(drawdown, crash_manager):
    st.subheader("⚠️ Crash / Recovery Signals")
    signal = crash_manager.get_signal(drawdown)
    st.write(f"**Crash Signal:** {signal if signal else 'No crash signal'}")

# src/dashboard/components/sync_fidelity.py
# 👉 Lets you upload your real Fidelity CSV and auto-detects drift

import streamlit as st
import json

from src.dashboard.components.drift_analysis import analyze_drift, render_drift_analysis
from src.engine.portfolio_parser import FidelityParser


def render_sync_fidelity(portfolio, portfolio_file):
    # -------------------------
    # INITIALIZE PARSER
    # -------------------------
    parser = FidelityParser()
    # -------------------------
    # INITIALIZE SESSION STATE
    # -------------------------
    if "fidelity_portfolio" not in st.session_state:
        st.session_state.fidelity_portfolio = None

    # -------------------------
    # PANEL STYLING & CONTAINER
    # -------------------------
    with st.container(border=True):
        st.subheader("📤 Sync with Fidelity")

        show_drift = st.checkbox("Show Drift Analysis Table", value=True)

        uploaded_file = st.file_uploader("Upload Fidelity Positions CSV", type=["csv"])

        # Update session state if a new file is uploaded
        if uploaded_file:
            fidelity_portfolio = parser.parse(uploaded_file)
            if fidelity_portfolio is not None:
                st.session_state.fidelity_portfolio = fidelity_portfolio
                st.success("✅ Fidelity data updated successfully!")
            else:
                st.error("❌ Failed to parse Fidelity CSV. Please ensure you are uploading the correct 'Positions' export.")

        # -------------------------
        # PERSISTENT DATA RENDERING
        # -------------------------
        if st.session_state.fidelity_portfolio is not None:
            fidelity_portfolio = st.session_state.fidelity_portfolio
            
            # --- DRIFT ANALYSIS ---
            drift_df = analyze_drift(portfolio, fidelity_portfolio)

            if show_drift:
                render_drift_analysis(drift_df)
            
            with st.expander("🔍 View Raw Comparison Data (Debug)"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Fidelity Data (CSV):**")
                    st.json(fidelity_portfolio)
                with col2:
                    st.write("**System Data (Current):**")
                    st.json(portfolio)

            # --- SYNC ACTION ---
            st.markdown("### ⚙️ Sync Actions")
            col_sync, col_clear = st.columns(2)

            with col_sync:
                if st.button("🔄 Sync Portfolio to Fidelity", width="stretch"):
                    with open(portfolio_file, "w") as f:
                        json.dump(fidelity_portfolio, f, indent=2)
                    st.success("✅ Portfolio successfully synced!")

            with col_clear:
                if st.button("🗑️ Clear Cached Fidelity Data", width="stretch"):
                    st.session_state.fidelity_portfolio = None
                    st.rerun()

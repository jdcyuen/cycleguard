# src/dashboard/components/sync_fidelity.py
# 👉 Lets you upload your real Fidelity CSV and auto-detects drift

import streamlit as st
import json
import os
import shutil
import glob
from datetime import datetime, timedelta

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

        uploaded_file = st.file_uploader("Upload Fidelity Positions CSV", type=["csv"])

        # Update session state if a new file is uploaded
        if uploaded_file:
            fidelity_portfolio = parser.parse(uploaded_file)
            if fidelity_portfolio is not None:
                st.session_state.fidelity_portfolio = fidelity_portfolio
                st.success("✅ Fidelity data updated successfully!")
            else:
                st.error(
                    "❌ Failed to parse Fidelity CSV. Please ensure you are uploading the correct 'Positions' export."
                )

        if st.session_state.get("sync_success"):
            st.success("✅ Portfolio successfully synced! Dashboard refreshed.")
            st.session_state.sync_success = False

        # -------------------------
        # DRIFT ANALYSIS DELEGATION
        # -------------------------
        comparison_portfolio = (
            st.session_state.fidelity_portfolio
            if st.session_state.fidelity_portfolio is not None
            else portfolio
        )
        render_drift_analysis(portfolio, comparison_portfolio, portfolio_file)

        if st.session_state.fidelity_portfolio is not None:
            fidelity_portfolio = st.session_state.fidelity_portfolio
            # --- SYNC ACTION ---
            st.markdown("### ⚙️ Sync Actions")
            col_sync, col_clear = st.columns(2)

            with col_sync:
                if st.button("🔄 Sync Portfolio to Fidelity", use_container_width=True):
                    # 1. Archive current state to ledger
                    history_dir = os.path.join(
                        os.path.dirname(portfolio_file), "history"
                    )
                    os.makedirs(history_dir, exist_ok=True)
                    if os.path.exists(portfolio_file):
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        archive_path = os.path.join(
                            history_dir, f"portfolio_{timestamp}.json"
                        )
                        shutil.copy2(portfolio_file, archive_path)

                    # 2. Save new state
                    with open(portfolio_file, "w") as f:
                        json.dump(fidelity_portfolio, f, indent=2)
                    st.cache_data.clear()
                    st.session_state.sync_success = True
                    st.rerun()

            with col_clear:
                if st.button("🗑️ Clear Cached Fidelity Data", use_container_width=True):
                    st.session_state.fidelity_portfolio = None
                    st.rerun()

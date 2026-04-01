# src/dashboard/components/sync_fidelity.py
# 👉 Lets you upload your real Fidelity CSV and auto-detects drift

import streamlit as st
import pandas as pd
import json

from src.dashboard.components.drift_analysis import analyze_drift, render_drift_analysis


def parse_fidelity_csv(file):
    df = pd.read_csv(file)

    # Normalize column names
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    if "symbol" not in df.columns or "current_value" not in df.columns:
        st.error("CSV must contain 'Symbol' and 'Current Value'")
        return None

    return dict(zip(df["symbol"], df["current_value"]))


def render_sync_fidelity(portfolio, portfolio_file):
    # -------------------------
    # PANEL STYLING & CONTAINER
    # -------------------------
    with st.container(border=True):
        st.subheader("📤 Sync with Fidelity")

        uploaded_file = st.file_uploader("Upload Fidelity Positions CSV", type=["csv"])

        if uploaded_file:
            fidelity_portfolio = parse_fidelity_csv(uploaded_file)

            if fidelity_portfolio:
                # -------------------------
                # DRIFT ANALYSIS (MODULAR)
                # -------------------------
                drift_df = analyze_drift(portfolio, fidelity_portfolio)
                render_drift_analysis(drift_df)

                # -------------------------
                # SYNC ACTION
                # -------------------------
                st.markdown("### ⚙️ Sync Actions")

                if st.button("🔄 Sync Portfolio to Fidelity"):
                    with open(portfolio_file, "w") as f:
                        json.dump(fidelity_portfolio, f, indent=2)

                    st.success("✅ Portfolio successfully synced to Fidelity data")

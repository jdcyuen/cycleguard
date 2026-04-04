# src/dashboard/components/sync_fidelity.py
# 👉 Lets you upload your real Fidelity CSV and auto-detects drift

import streamlit as st
import pandas as pd
import json

from src.dashboard.components.drift_analysis import analyze_drift, render_drift_analysis


def parse_fidelity_csv(file):
    try:
        # Fidelity CSVs often have metadata at the top.
        # We need to find the header row containing 'Symbol' and 'Current Value'.
        file.seek(0)
        lines = file.readlines()

        header_index = -1
        for i, line in enumerate(lines):
            # Normalizing to help with detection
            decoded_line = (
                line.decode("utf-8").lower()
                if isinstance(line, bytes)
                else line.lower()
            )
            if "symbol" in decoded_line and "current value" in decoded_line:
                header_index = i
                break

        if header_index == -1:
            st.error("No valid 'Symbol' and 'Current Value' headers found in CSV.")
            return None

        # Rewind and read with header offset
        # We use sep=None to auto-detect the separator (comma vs. tab)
        # and engine='python' for more flexible parsing.
        file.seek(0)
        df = pd.read_csv(
            file, skiprows=header_index, sep=None, on_bad_lines="skip", engine="python"
        )

        # Normalize column names
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

        if "symbol" not in df.columns or "current_value" not in df.columns:
            st.error("CSV must contain 'Symbol' and 'Current Value'")
            return None

        # Clean symbols (remove whitespace/non-ticker text)
        df["symbol"] = df["symbol"].astype(str).str.strip()

        # Clean current_value (remove $, commas, and non-numeric characters)
        if df["current_value"].dtype == "object":
            df["current_value"] = (
                df["current_value"]
                .astype(str)
                .str.replace("$", "", regex=False)
                .str.replace(",", "", regex=False)
                .str.extract(r"(\d+\.?\d*)")
                .astype(float)
            )

        # Filter out rows without valid symbols or values
        df = df.dropna(subset=["symbol", "current_value"])

        # Group by symbol in case of duplicate entries
        portfolio = df.groupby("symbol")["current_value"].sum().to_dict()

        return portfolio

    except Exception as e:
        st.error(f"Failed to parse CSV: {e}")
        return None


def render_sync_fidelity(portfolio, portfolio_file):
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
            fidelity_portfolio = parse_fidelity_csv(uploaded_file)
            if fidelity_portfolio is not None:
                st.session_state.fidelity_portfolio = fidelity_portfolio
                st.success("✅ Fidelity data updated successfully!")

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

# src/dashboard/components/drift_analysis.py
# 👉 This compares your system portfolio vs. Fidelity’s real holdings


import streamlit as st
import pandas as pd


def analyze_drift(system_portfolio, fidelity_portfolio):
    drift_data = []

    all_tickers = set(system_portfolio.keys()).union(fidelity_portfolio.keys())

    for ticker in all_tickers:
        system_value = system_portfolio.get(ticker, 0)
        fidelity_value = fidelity_portfolio.get(ticker, 0)

        diff = fidelity_value - system_value

        pct_diff = 0
        if system_value != 0:
            pct_diff = diff / system_value
        elif fidelity_value != 0:
            pct_diff = 1.0

        drift_data.append(
            {
                "Ticker": ticker,
                "System ($)": system_value,
                "Fidelity ($)": fidelity_value,
                "Difference ($)": diff,
                "Difference (%)": pct_diff,
            }
        )

    df = pd.DataFrame(drift_data)

    return df


def render_drift_analysis(drift_df):

    # -------------------------
    # PANEL STYLING & CONTAINER
    # -------------------------
    with st.container(border=True):
        st.markdown("### 🔍 Drift Detection")

        st.dataframe(
            drift_df.style.format(
                {
                    "System ($)": "${:,.2f}",
                    "Fidelity ($)": "${:,.2f}",
                    "Difference ($)": "${:,.2f}",
                    "Difference (%)": "{:.2%}",
                }
            )
        )

        # Significant drift
        large_drift = drift_df[drift_df["Difference (%)"].abs() > 0.05]

        if not large_drift.empty:
            st.warning("⚠️ Significant drift detected (>5%)")
        else:
            st.success("✅ Portfolio is closely aligned")

        # New positions
        new_positions = drift_df[
            (drift_df["System ($)"] == 0) & (drift_df["Fidelity ($)"] > 0)
        ]

        if not new_positions.empty:
            st.warning("🆕 New positions found in Fidelity (not in system):")
            for ticker in new_positions["Ticker"]:
                st.write(f"• {ticker}")

        # Missing positions
        missing_positions = drift_df[
            (drift_df["System ($)"] > 0) & (drift_df["Fidelity ($)"] == 0)
        ]

        if not missing_positions.empty:
            st.warning("❌ Positions missing from Fidelity (still in system):")
            for ticker in missing_positions["Ticker"]:
                st.write(f"• {ticker}")

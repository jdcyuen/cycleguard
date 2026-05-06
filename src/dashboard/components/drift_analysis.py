# src/dashboard/components/drift_analysis.py
# 👉 This compares your system portfolio vs. Fidelity’s real holdings


import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
import os
import glob
import json
from datetime import datetime, timedelta


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
                "Selected Anchor ($)": system_value,
                "Fidelity ($)": fidelity_value,
                "Difference ($)": diff,
                "Diff (%/$)": pct_diff,
            }
        )

    df = pd.DataFrame(drift_data)

    return df


def render_drift_analysis(portfolio, comparison_portfolio, portfolio_file):
    # -------------------------
    # PANEL STYLING & CONTAINER
    # -------------------------
    with st.container(border=True):
        st.markdown("### 🔍 Drift Detection")

        # --- HISTORICAL BASELINE SELECTION ---
        history_dir = os.path.join(os.path.dirname(portfolio_file), "history")
        historical_files = []
        if os.path.exists(history_dir):
            historical_files = sorted(
                glob.glob(os.path.join(history_dir, "portfolio_*.json"))
            )

        baseline_options = ["Standard (Previous Sync)"]
        baseline_options.extend(
            ["7 Days Ago", "14 Days Ago", "21 Days Ago", "30 Days Ago"]
        )

        selected_baseline = st.selectbox(
            "🔬 Select Drift Baseline Analysis Depth:", baseline_options
        )

        baseline_portfolio = portfolio  # default to last sync
        if selected_baseline != "Standard (Previous Sync)" and historical_files:
            target_days = int(selected_baseline.split()[0])
            target_date = datetime.now() - timedelta(days=target_days)
            best_file = historical_files[0]
            min_diff = None
            for h_file in historical_files:
                basename = os.path.basename(h_file)
                try:
                    ts_str = basename.replace("portfolio_", "").replace(".json", "")
                    f_date = datetime.strptime(ts_str, "%Y%m%d_%H%M%S")
                    diff = abs((f_date - target_date).total_seconds())
                    if min_diff is None or diff < min_diff:
                        min_diff = diff
                        best_file = h_file
                except Exception:
                    continue
            try:
                with open(best_file, "r") as f:
                    baseline_portfolio = json.load(f)
                best_basename = os.path.basename(best_file)
                try:
                    actual_ts = best_basename.replace("portfolio_", "").replace(
                        ".json", ""
                    )
                    actual_date = datetime.strptime(actual_ts, "%Y%m%d_%H%M%S")
                    actual_days_ago = (datetime.now() - actual_date).days
                    if abs(actual_days_ago - target_days) > 2:
                        st.caption(
                            f"⚠️ *Note: Did not find exact date. Using closest available baseline from ~{actual_days_ago} days ago.*"
                        )
                    else:
                        st.caption(
                            f"✅ *Comparing securely against target baseline from ~{actual_days_ago} days ago.*"
                        )
                except Exception:
                    pass
            except Exception:
                pass

        # Calculate Drift
        drift_df = analyze_drift(baseline_portfolio, comparison_portfolio)

        if drift_df.empty:
            st.warning(
                "⚠️ No tickers found to analyze. Please ensure your Fidelity CSV contains data."
            )
            return

        st.write(f"Showing comparison for **{len(drift_df)}** tickers.")

        gb = GridOptionsBuilder.from_dataframe(drift_df)

        # Format Currency Columns
        currency_formatter = JsCode("""
        function(params) {
            if (params.value === null || params.value === undefined) return '';
            return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(params.value);
        }
        """)

        # Format Compound Diff Column (Sorted via underlying percentage!)
        diff_formatter = JsCode("""
        function(params) {
            if (params.value === null || params.value === undefined) return '';
            const pct = (params.value * 100).toFixed(2);
            const pctSign = params.value > 0 ? '+' : '';
            const rawDiff = params.data['Difference ($)'] || 0;
            let moneyStr = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(rawDiff);
            if (rawDiff > 0) {
                moneyStr = '+' + moneyStr;
            }
            return pctSign + pct + '% / ' + moneyStr;
        }
        """)

        gb.configure_column(
            "Selected Anchor ($)",
            valueFormatter=currency_formatter,
            type=["numericColumn", "numberColumnFilter"],
        )
        gb.configure_column(
            "Fidelity ($)",
            valueFormatter=currency_formatter,
            type=["numericColumn", "numberColumnFilter"],
        )

        # We sort by Diff (%/$) natively because the Python column natively outputs the raw Float pct_diff to the client
        gb.configure_column(
            "Diff (%/$)",
            valueFormatter=diff_formatter,
            type=["numericColumn", "numberColumnFilter"],
            sort="desc",
        )

        # Hide the raw dollar diff column from the UI
        gb.configure_column("Difference ($)", hide=True)

        gridOptions = gb.build()

        AgGrid(
            drift_df,
            gridOptions=gridOptions,
            allow_unsafe_jscode=True,
            fit_columns_on_grid_load=True,
            theme="streamlit",
        )

        # Significant drift
        large_drift = drift_df[drift_df["Diff (%/$)"].abs() > 0.05]
        large_drift_tickers = large_drift["Ticker"].tolist()

        if not large_drift.empty:
            st.warning(
                f"⚠️ **{len(large_drift)}** Significant drift(s) detected (>5%), tickers: {large_drift_tickers}"
            )
        else:
            st.success("✅ Portfolio is closely aligned.")

        with st.expander("🔍 View Raw Comparison Drift Dectection Data (Debug)"):
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Comparison Data (CSV or Local):**")
                st.json(comparison_portfolio)
            with col2:
                st.write("**System Baseline (Anchor):**")
                st.json(baseline_portfolio)

        # New positions
        new_positions = drift_df[
            (drift_df["Selected Anchor ($)"] == 0) & (drift_df["Fidelity ($)"] > 0)
        ]

        if not new_positions.empty:
            st.warning(
                f"🆕 **{len(new_positions)}** New positions found in latest reading (not in system baseline):"
            )
            for ticker in new_positions["Ticker"]:
                st.write(f"• {ticker}")

        # Missing positions
        missing_positions = drift_df[
            (drift_df["Selected Anchor ($)"] > 0) & (drift_df["Fidelity ($)"] == 0)
        ]

        if not missing_positions.empty:
            st.warning(
                f"❌ **{len(missing_positions)}** Positions missing from latest reading (still in system baseline):"
            )
            for ticker in missing_positions["Ticker"]:
                st.write(f"• {ticker}")

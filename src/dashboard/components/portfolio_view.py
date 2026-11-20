# src/dashboard/components/portfolio_view.py

import json
import pandas as pd
from st_aggrid import (
    AgGrid,
    GridOptionsBuilder,
    ColumnsAutoSizeMode,
    JsCode,
)
import streamlit as st

PORTFOLIO_ACCOUNT_COLORS = [
    "#EAF2F8",  # Light blue
    "#EAF4EA",  # Light green
    "#FFF4E5",  # Light orange
    "#F3ECF8",  # Light purple
    "#FCEDEE",  # Light rose
    "#E8F4F4",  # Light teal
    "#F5F1E8",  # Light beige
    "#EEF0F5",  # Light slate
]

def _render_portfolio_loading_overlay():
    st.html(
        """
        <style>
		.st-key-portfolio_view_panel {
			position: relative;
			min-height: 550px;
		}

		.st-key-portfolio_view_panel [data-testid="stEmpty"] {
			position: absolute;
			inset: 0;
			z-index: 999999;
		}
        .portfolio-loading-overlay {
			position: absolute;
			inset: 0;
			min-height: 550px;
			width: 100%;
			box-sizing: border-box;
			z-index: 999999;
			background: rgba(255, 255, 255, 0.88);
			display: flex;
			align-items: center;
			justify-content: center;
			flex-direction: column;
		}

		.portfolio-loading-spinner {
			position: relative;
			width: 84px;
			height: 84px;
			animation: portfolio-orbit 2.4s linear infinite;
		}

		.portfolio-loading-spinner .orbit-dot {
			position: absolute;
			width: 11px;
			height: 11px;
			border-radius: 50%;
			background: #1677c8;
			left: 36.5px;
			top: 0;
		}

		.portfolio-loading-spinner .orbit-dot:nth-child(1) {
			opacity: 1;
		}

		.portfolio-loading-spinner .orbit-dot:nth-child(2) {
			transform: rotate(45deg) translateY(-36.5px);
			opacity: 0.9;
		}

		.portfolio-loading-spinner .orbit-dot:nth-child(3) {
			transform: rotate(90deg) translateY(-36.5px);
			opacity: 0.8;
		}

		.portfolio-loading-spinner .orbit-dot:nth-child(4) {
			transform: rotate(135deg) translateY(-36.5px);
			opacity: 0.7;
		}

		.portfolio-loading-spinner .orbit-dot:nth-child(5) {
			transform: rotate(180deg) translateY(-36.5px);
			opacity: 0.6;
		}

		.portfolio-loading-spinner .orbit-dot:nth-child(6) {
			transform: rotate(225deg) translateY(-36.5px);
			opacity: 0.5;
		}

		.portfolio-loading-spinner .orbit-dot:nth-child(7) {
			transform: rotate(270deg) translateY(-36.5px);
			opacity: 0.4;
		}

		.portfolio-loading-spinner .orbit-dot:nth-child(8) {
			transform: rotate(315deg) translateY(-36.5px);
			opacity: 0.3;
		}

        .portfolio-loading-text {
            margin-top: 20px;
            font-size: 21px;
            font-weight: 600;
            color: #17324d;
        }

		@keyframes portfolio-orbit {
			from { transform: rotate(0deg); }
			to { transform: rotate(360deg); }
		}
        </style>

        <div class="portfolio-loading-overlay">
            <div class="portfolio-loading-spinner">
			<div class="orbit-dot"></div>
			<div class="orbit-dot"></div>
			<div class="orbit-dot"></div>
			<div class="orbit-dot"></div>
			<div class="orbit-dot"></div>
			<div class="orbit-dot"></div>
			<div class="orbit-dot"></div>
			<div class="orbit-dot"></div>
		</div>
            <div class="portfolio-loading-text">
                Loading Portfolio View...
            </div>
        </div>
        """,
    )

def render_portfolio_view(portfolio, portfolio_view_service=None):
    with st.container(border=True, key="portfolio_view_panel"):
        overlay_placeholder = st.empty()

        with overlay_placeholder.container():
            _render_portfolio_loading_overlay()

        _render_portfolio_view_content(
            portfolio,
            portfolio_view_service,
        )

        overlay_placeholder.empty()


def _render_portfolio_view_content(
    portfolio,
    portfolio_view_service=None,
):
    st.subheader("📊 Portfolio Overview")

    if portfolio_view_service is None:
        st.error("Portfolio View service is not available.")
        return

    try:
        available_accounts = portfolio_view_service.list_accounts()

        if not available_accounts:
            st.info("No active accounts available.")
            return

        account_options = {
            "All Accounts": None,
        }

        for account in available_accounts:
            account_options[
                account.account_config.display_name
            ] = account.database_account.id

        account_labels = list(account_options.keys())

        dropdown_width = max(
            200,
            max(len(label) for label in account_labels) * 8 + 48,
        )

        selected_account = st.selectbox(
            "Select Account",
            options=account_labels,
            key="portfolio_view_account_selector",
            width=dropdown_width,
        )

        selected_account_id = account_options[selected_account]

        if selected_account_id is None:
            portfolio_result = (
                portfolio_view_service.build_all_accounts_view()
            )
        else:
            account_view = (
                portfolio_view_service.build_account_view(
                    selected_account_id
                )
            )

            from models.portfolio_view import PortfolioViewResult

            portfolio_result = PortfolioViewResult(
                selected_account_id=selected_account_id,
                accounts=[account_view],
                holdings=account_view.holdings,
                actual_allocations=account_view.actual_allocations,
                target_allocations=account_view.target_allocations,
                validation_warnings=account_view.validation_warnings,
                actual_allocation_complete=(
                    account_view.snapshot is not None
                ),
            )

        if portfolio_result.missing_snapshot_accounts:
            st.warning(
                "Missing portfolio snapshots: "
                + ", ".join(
                    portfolio_result.missing_snapshot_accounts
                )
            )

        for warning in portfolio_result.validation_warnings:
            st.warning(warning)

        if not portfolio_result.actual_allocation_complete:
            st.warning(
                "Actual allocations are incomplete because one or "
                "more account snapshots are unavailable."
            )

        if not portfolio_result.holdings:
            st.info("No holdings are available for the selected view.")
            return

        symbols = [
            holding.position.symbol
            for holding in portfolio_result.holdings
        ]

        year_ranges = (
            portfolio_view_service.fetch_52_week_ranges(symbols)
        )

        # Map each account name to its effective snapshot date.
        snapshot_dates = {
            account_view.account_config.display_name: (
                account_view.snapshot.snapshot_date.strftime("%b %d, %Y")
                if (
                    account_view.snapshot is not None
                    and account_view.snapshot.snapshot_date is not None
                )
                else "Missing Snapshot"
            )
            for account_view in portfolio_result.accounts
        }

        data = []

        for holding in portfolio_result.holdings:
            row = {
                "Symbol": holding.position.symbol,
                "Bucket": (
                    ""
                    if holding.bucket == "UNMAPPED"
                    else holding.bucket
                ),
                "Quantity": (
                    float(holding.position.quantity)
                    if holding.position.quantity is not None
                    else None
                ),
                "Last Price": (
                    float(holding.position.last_price)
                    if holding.position.last_price is not None
                    else None
                ),
                "Current Value": float(
                    holding.position.current_value
                ),
                "Total Gain/Loss ($)": (
                    float(holding.position.total_gain)
                    if holding.position.total_gain is not None
                    else None
                ),
                "Total Gain/Loss (%)": (
                    float(holding.position.total_gain_pct)
                    if holding.position.total_gain_pct is not None
                    else None
                ),
                "Percent of Account": (
                    float(holding.position.percent_of_account) / 100
                    if holding.position.percent_of_account is not None
                    else None
                ),
                "Snapshot Date": snapshot_dates.get(
                    holding.account_name,
                    "Missing Snapshot",
                ),
            }

            if selected_account_id is None:
                row["Account"] = (
                    holding.account_name or "Unknown Account"
                )

            row["52-Week Low"] = year_ranges.get(
                holding.position.symbol.strip().upper(),
                {},
            ).get("year_low")

            row["52-Week High"] = year_ranges.get(
                holding.position.symbol.strip().upper(),
                {},
            ).get("year_high")

            data.append(row)

        df = pd.DataFrame(data)

        total_value = df["Current Value"].sum()

        if selected_account_id is None:
            st.caption(
                f"**Combined Market Value:** ${total_value:,.2f} "
                f"| **Holdings:** {len(df)} "
                f"| **Accounts:** {len(portfolio_result.accounts)}"
            )
        else:
            st.caption(
                f"**Total Portfolio Value:** ${total_value:,.2f} "
                f"| **Holdings:** {len(df)}"
            )

        # Build a stable account-to-color mapping for All Accounts.
        account_colors = {}

        if selected_account_id is None:
            account_names = sorted(df["Account"].unique())

            account_colors = {
                account_name: PORTFOLIO_ACCOUNT_COLORS[
                    index % len(PORTFOLIO_ACCOUNT_COLORS)
                ]
                for index, account_name in enumerate(account_names)
            }

        gb = GridOptionsBuilder.from_dataframe(df)

        gb.configure_column(
            "Symbol",
            header_name="Ticker",
            pinned="left",
            filter=True,
            cellStyle={
                "fontWeight": "bold",
                "color": "#00d4ff",
            },
        )

        gb.configure_column(
            "Current Value",
            header_name="Current Value ($)",
            type=["numericColumn", "numberColumnFilter"],
            valueFormatter=(
                "x.toLocaleString('en-US', "
                "{style: 'currency', currency: 'USD'})"
            ),
        )

        gb.configure_column(
            "Last Price",
            header_name="Last Price ($)",
            type=["numericColumn", "numberColumnFilter"],
            valueFormatter=(
                "x == null ? '' : "
                "x.toLocaleString('en-US', "
                "{style: 'currency', currency: 'USD'})"
            ),
        )

        gb.configure_column(
            "Percent of Account",
            header_name="% of Account",
            type=["numericColumn"],
            valueFormatter=(
                "x == null ? '' : (x * 100).toFixed(2) + '%'"
            ),
        )

        gb.configure_column(
            "Snapshot Date",
            header_name="Snapshot Date",
            filter=True,
            sortable=True,
        )

        if selected_account_id is None:
            gb.configure_column(
                "Account",
                header_name="Account",
                filter=True,
                sortable=True,
            )

            get_row_style = JsCode(
                f"""
                function(params) {{
                    const accountColors = {json.dumps(account_colors)};
                    const account = params.data.Account;

                    return {{
                        backgroundColor:
                            accountColors[account] || '#FFFFFF'
                    }};
                }}
                """
            )

            gb.configure_grid_options(
                getRowStyle=get_row_style
            )

        gb.configure_column(
            "52-Week Low",
            header_name="52-Week Low ($)",
            type=["numericColumn"],
            valueFormatter=(
                "x == null ? '' : x.toLocaleString('en-US', "
                "{style: 'currency', currency: 'USD'})"
            ),
        )

        gb.configure_column(
            "52-Week High",
            header_name="52-Week High ($)",
            type=["numericColumn"],
            valueFormatter=(
                "x == null ? '' : x.toLocaleString('en-US', "
                "{style: 'currency', currency: 'USD'})"
            ),
        )

        grid_options = gb.build()

        AgGrid(
            df.sort_values(
                "Current Value",
                ascending=False,
            ),
            gridOptions=grid_options,
            theme="alpine",
            height=350,
            columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
            allow_unsafe_jscode=True,
        )
    except Exception as exc:
        st.exception(exc)

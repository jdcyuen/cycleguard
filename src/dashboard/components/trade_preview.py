# src/dashboard/components/trade_preview.py
# 👉 Shows you exactly what will execute before you click “Run”


import streamlit as st


def render_trade_preview(
    portfolio,
    latest_market,
    crash_manager,
    config,
    phase_data=None,
    crash_decision=None,
):
    # Panel styling & container
    with st.container(border=True):
        st.subheader("📋 Trade Preview")

        total_value = sum(portfolio.values())
        drawdown = latest_market.get("drawdown", 0)

        signal = crash_decision if crash_decision and crash_decision.action == "DEPLOY" else None

        if not signal:
            if phase_data and phase_data.get("regime") == "RISK_ON":
                funding_priority = config.get("funding", {}).get("priority", [])
                discretionary_cash = sum(portfolio.get(ticker, 0) for ticker in funding_priority)
                target_cash_limit = 0.15 * total_value
                surplus = max(0, discretionary_cash - target_cash_limit)

                if surplus > 0:
                    st.write(f"**Signal:** Cash Drag Redeployment")
                    st.write(f"**Deploy Amount:** ${surplus:,.0f}")
                    
                    st.markdown("### 🔻 Sell (Funding)")
                    remaining_surplus = surplus
                    sell_orders = []
                    for asset in funding_priority:
                        if remaining_surplus <= 0:
                            break
                        available = portfolio.get(asset, 0)
                        sell_amount = min(available, remaining_surplus)
                        if sell_amount > 0:
                            sell_orders.append((asset, sell_amount))
                            remaining_surplus -= sell_amount

                    for asset, amt in sell_orders:
                        st.write(f"SELL {asset}: ${amt:,.0f}")

                    st.markdown("### 🟢 Buy (Deployment)")
                    return

            st.write("🟢 No trades needed at this time")
            return

        deploy_pct = crash_decision.deployment_pct
        deploy_amount = crash_decision.deployment_amount

        st.write(f"**Signal:** {signal}")
        st.write(f"**Deploy Amount:** ${deploy_amount:,.0f}")

        # -------------------------
        # FUNDING (SELL SIDE)
        # -------------------------
        st.markdown("### 🔻 Sell (Funding)")

        funding_priority = config.get("funding", {}).get("priority", [])
        remaining = deploy_amount
        sell_orders = []

        for asset in funding_priority:
            if remaining <= 0:
                break

            available = portfolio.get(asset, 0)
            sell_amount = min(available, remaining)

            if sell_amount > 0:
                sell_orders.append((asset, sell_amount))
                remaining -= sell_amount

        for asset, amt in sell_orders:
            st.write(f"SELL {asset}: ${amt:,.0f}")

        # -------------------------
        # BUY SIDE
        # -------------------------
        st.markdown("### 🟢 Buy (Deployment)")

        

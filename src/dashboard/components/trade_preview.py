# src/dashboard/components/trade_preview.py
# 👉 Shows you exactly what will execute before you click “Run”


import streamlit as st


def render_trade_preview(portfolio, latest_market, crash_manager, config):
    # Panel styling & container
    with st.container(border=True):
        st.subheader("📋 Trade Preview")

        total_value = sum(portfolio.values())
        drawdown = latest_market.get("drawdown", 0)

        signal = crash_manager.get_signal(drawdown)

        if not signal:
            st.write("🟢 No trades needed at this time")
            return

        deployment_levels = config.get("deployment", {}).get("levels", {})
        deploy_pct = deployment_levels.get(signal, 0)
        deploy_amount = total_value * deploy_pct

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

        buy_targets = config.get("buy_targets", {}).get(signal, {})

        buy_orders = []
        for asset, weight in buy_targets.items():
            buy_amount = deploy_amount * weight
            buy_orders.append((asset, buy_amount))

        for asset, amt in buy_orders:
            st.write(f"BUY {asset}: ${amt:,.0f}")

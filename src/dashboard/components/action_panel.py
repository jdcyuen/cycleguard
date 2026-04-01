# src/dashboard/components/action_panel.py
# 👉 This is your “What Should I Do Today?” brain


import streamlit as st


def render_action_panel(
    portfolio,
    latest_market,
    crash_manager,
    recovery_manager,
    config,
    load_rebalance_state,
):
    # -------------------------
    # PANEL STYLING & CONTAINER
    # -------------------------
    with st.container(border=True):
        st.subheader("🧠 What Should I Do Today?")

        total_value = sum(portfolio.values())
        drawdown = latest_market.get("drawdown", 0)
        current_price = latest_market.get("close", 0)

        signal = crash_manager.get_signal(drawdown)

        action_text = ""
        details = []

        # -------------------------
        # CRASH ACTIONS
        # -------------------------
        if signal:
            deployment_levels = config.get("deployment", {}).get("levels", {})
            deploy_pct = deployment_levels.get(signal, 0)

            deploy_amount = total_value * deploy_pct

            action_text = f"⚠️ {signal} Triggered"

            # Funding sources
            funding_priority = config.get("funding", {}).get("priority", [])
            if funding_priority:
                details.append(f"Sell from: {', '.join(funding_priority[:2])}")

            # Deployment
            details.append(f"Deploy approximately **${deploy_amount:,.0f}** into equities")

            # Buy targets
            buy_targets = config.get("buy_targets", {}).get(signal, {})
            if buy_targets:
                top_targets = list(buy_targets.keys())[:3]
                details.append(f"Buy priority: {', '.join(top_targets)}")

        # -------------------------
        # RECOVERY ACTIONS
        # -------------------------
        else:
            state = load_rebalance_state()

            recovery_cfg = config.get("recovery", {})
            rebound_threshold = recovery_cfg.get("rebound_threshold", 0.2)

            bottom = state.get("bottom")

            if bottom:
                rebound = (current_price - bottom) / bottom

                if rebound >= rebound_threshold:
                    action_text = "📈 Recovery Phase"

                    trim_targets = recovery_cfg.get("trim_targets", {})
                    for asset, pct in trim_targets.items():
                        details.append(f"Trim {asset} by {int(pct * 100)}%")

                    cash_target = recovery_cfg.get("rebuild_cash_to", "cash")
                    details.append(f"Move proceeds to {cash_target}")

                    details.append(f"Rebound from bottom: {rebound:.2%}")

                else:
                    action_text = "🟢 No Action Needed"
                    details.append(f"Rebound from bottom: {rebound:.2%} (below threshold)")

            else:
                action_text = "🟢 No Action Needed"
                details.append("No market bottom detected yet")

        # -------------------------
        # DISPLAY
        # -------------------------
        st.markdown(f"### {action_text}")

        for d in details:
            st.write(f"• {d}")

        # -------------------------
        # DEBUG PANEL
        # -------------------------
        with st.expander("🔍 Debug Info"):
            st.write(f"Total Portfolio Value: ${total_value:,.2f}")
            st.write(f"Drawdown: {drawdown:.2%}")
            st.write(f"Signal: {signal}")

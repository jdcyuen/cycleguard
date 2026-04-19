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
    phase_data,
):
    # -------------------------
    # PANEL STYLING & CONTAINER
    # -------------------------
    with st.container(border=True):
        st.subheader("🧠 What Should I Do Today?")

        total_value = sum(portfolio.values())
        drawdown = latest_market.get("drawdown", 0)
        current_price = latest_market.get("close", 0)
        
        # Cash Drag Global Variables
        funding_priority = config.get("funding", {}).get("priority", [])
        discretionary_cash = sum(portfolio.get(ticker, 0) for ticker in funding_priority)
        target_cash_limit = 0.15 * total_value
        surplus = max(0, discretionary_cash - target_cash_limit)

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
                regime = phase_data.get("regime", "UNKNOWN")
                if regime == "RISK_ON":
                    action_text = "🟢 Optimal Growth Climate"
                    details.append("Macro environment is highly favorable. Maintain core equity exposure.")
                    
                    # Cash Drag Redeployment Logic
                    if discretionary_cash > target_cash_limit:
                        details.append(f"⚠️ **Cash Drag Warning:** You hold **\${discretionary_cash:,.0f}** in discretionary defensive assets ({(discretionary_cash/total_value):.1%}).")
                        
                        sell_orders = {}
                        remaining_surplus = surplus
                        for ticker in funding_priority:
                            amount_held = portfolio.get(ticker, 0)
                            if amount_held > 0:
                                sell_amt = min(remaining_surplus, amount_held)
                                sell_orders[ticker] = sell_amt
                                remaining_surplus -= sell_amt
                                if remaining_surplus <= 0:
                                    break
                                    
                        sell_str = " | ".join([f"Sell {t}: \${amt:,.0f}" for t, amt in sell_orders.items()])
                        details.append(f"**Recommended Action:** Systematically redeploy your **\${surplus:,.0f}** surplus into core equities over the next 4-8 weeks.")
                        details.append(f"**Funding Order:** {sell_str}")
                        
                        # Generate Buy targets using Level 1 core weights as default
                        buy_targets = config.get("buy_targets", {}).get("Level 1", {})
                        if buy_targets:
                            buy_str = " | ".join([f"Buy {t}: \${(surplus * weight):,.0f}" for t, weight in buy_targets.items()])
                            details.append(f"**Deployment Targets:** {buy_str}")
                    else:
                        details.append(f"✅ Discretionary cash is perfectly optimized at {(discretionary_cash/total_value):.1%} (${discretionary_cash:,.0f}).")
                elif regime == "DEFENSIVE":
                    action_text = "🛡️ Capital Protection Phase"
                    details.append("Bearish metrics detected. Avoid massive new equity purchases.")
                    details.append(f"Hold Cash and wait for deep discounts or Trend recovery. (Score: {phase_data.get('score', 0)}/10)")
                else:
                    action_text = "🟡 Transition Phase"
                    details.append("Market signals are currently mixed.")
                    details.append(f"Maintain current positions. Proceed with caution on new capital. (Score: {phase_data.get('score', 0)}/10)")

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
            st.write("---")
            st.write(f"**Funding Priority Accounts:** {', '.join(funding_priority)}")
            cash_breakdown = " + ".join([f"{t}: \${portfolio.get(t,0):,.0f}" for t in funding_priority if portfolio.get(t,0) > 0])
            st.write(f"**Discretionary Cash Amount:** \${discretionary_cash:,.2f} &nbsp;&nbsp; *( Breakdown: {cash_breakdown} )*")
            st.write(f"**Target 15% Cash Limit:** \${target_cash_limit:,.2f} &nbsp;&nbsp; *( 15% × Total Portfolio Value of \${total_value:,.0f} )*")
            st.write(f"**Calculated Cash Surplus:** \${surplus:,.2f} &nbsp;&nbsp; *( \${discretionary_cash:,.2f} - \${target_cash_limit:,.2f} )*")

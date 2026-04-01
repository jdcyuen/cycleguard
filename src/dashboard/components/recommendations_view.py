import streamlit as st
from src.dashboard.utils import load_recovery_state

def render_recommendations_view(portfolio, latest_market, config, crash_manager):
    st.subheader("🧠 What Should I Do Today?")

    total_value = sum(portfolio.values())
    signal = crash_manager.get_signal(latest_market["drawdown"])

    action_text = ""
    details = []

    # -------------------------
    # CRASH ACTIONS
    # -------------------------
    if signal:
        deploy_pct = config["deployment"]["levels"][signal]
        deploy_amount = total_value * deploy_pct

        action_text = f"⚠️ {signal} Triggered"

        # Funding sources
        funding = config["funding"]["priority"]

        details.append(f"Deploy approximately **${deploy_amount:,.0f}** into equities")
        details.append(f"Sell from: {', '.join(funding[:2])}")

        # Buy targets
        buy_targets = config["buy_targets"][signal]
        top_targets = list(buy_targets.keys())[:3]
        details.append(f"Buy priority: {', '.join(top_targets)}")

    # -------------------------
    # RECOVERY ACTIONS
    # -------------------------
    else:
        recovery_state = load_recovery_state()

        # Simple recovery check
        rebound_threshold = config["recovery"]["rebound_threshold"]
        bottom = recovery_state.get("bottom")

        if bottom:
            rebound = (latest_market["close"] - bottom) / bottom

            if rebound >= rebound_threshold:
                action_text = "📈 Recovery Phase"

                trim_targets = config["recovery"]["trim_targets"]
                for asset, pct in trim_targets.items():
                    details.append(f"Trim {asset} by {int(pct * 100)}%")

                details.append(f"Move proceeds to {config['recovery']['rebuild_cash_to']}")
            else:
                action_text = "🟢 No Action Needed"
        else:
            action_text = "🟢 No Action Needed"

    # -------------------------
    # DISPLAY
    # -------------------------
    st.markdown(f"### {action_text}")
    for d in details:
        st.write(f"• {d}")


E:\CycleGuard

Github repository
https://github.com/jdcyuen/cycleguard.git



🧠 CycleGuard — Daily & Operational Management
1️⃣ Daily Execution
● Purpose: Detect crash or recovery signals, rebalance portfolio, log trades.
● Script to run: daily_rebalance.py
● Frequency: Once per trading day (after market close) is sufficient.
    ● You want end-of-day prices for accurate drawdown calculations.
    ● Running intra-day is optional but may generate noise.

How to run:

    cd E:\CycleGuard
    python scripts\daily_rebalance.py
or
	streamlit run src/dashboard/cycleguard_dashboard.py

● This will:
1. Fetch latest S&P 500 / market data
2. Calculate drawdown and check crash signals
3. Execute trades if needed
4. Update portfolio state (portfolio_state.json)
5. Update trade log (trade_log.csv)
6. Apply recovery trims if conditions are met


#Run tests via:
python -m unittest tests/test_crash_manager.py



2️⃣ Automating Daily Execution

To avoid manual runs:

Windows (Task Scheduler)
1. Open Task Scheduler → Create Task
2. Trigger → Daily at 5:15 PM (or after market close)
3. Action → Start a program:
    Program/script: python
    Add arguments: E:\CycleGuard\scripts\daily_rebalance.py
    Start in: E:\CycleGuard
4. Optional: Set email alerts if a crash signal triggers.

Linux / macOS (Cron)
# Run at 5:15 PM every weekday
15 17 * * 1-5 /usr/bin/python3 /home/user/CycleGuard/scripts/daily_rebalance.py

3️⃣ Streamlit Dashboard
● Purpose: Visual overview of portfolio, drawdowns, and trades.
● Script: cycleguard_dashboard.py
● Frequency: Can leave it running continuously or refresh on demand.
● How to run:
    streamlit run src/dashboard/cycleguard_dashboard.py
● Open in browser → see portfolio, crash signals, recovery status, trade log
● Works offline, but ideally run on same machine as daily_rebalance.py

4️⃣ Managing Trades & Dry Powder
● Portfolio State: portfolio_state.json → always reflects current allocations
● Trade Log: trade_log.csv → keeps permanent record of executed trades
● Rebalance State: rebalance_state.json → tracks which crash levels have been executed
● Recovery State: recovery_state.json → tracks bottom/rebound adjustments

Tip: Do not manually edit JSON files unless correcting mistakes. Let the system handle the state.

5️⃣ Manual Intervention

You may need to intervene if:

1. Large unexpected market event — can temporarily pause automation.
2. New portfolio allocations — update config.yaml with new holdings or position limits.
3. System upgrade — update scripts or dependencies (requirements.txt)

6️⃣ Backtesting / Analysis
● Purpose: Compare strategy performance vs buy-and-hold.
● Script: backtests/backtest_engine.py
● Run periodically (e.g., monthly) to evaluate strategy effectiveness:
    python backtests/backtest_engine.py
● Outputs: equity curve, CAGR, Sharpe, drawdowns, trade summary

7️⃣ Maintenance Checklist
Task	                            Frequency
-----                               ----------
Run daily_rebalance.py	            Daily
Check dashboard	                    Daily / On-demand
Review trade log	                Weekly / Monthly
Update config.yaml	                As needed
Backtest strategy	                Monthly / Quarterly
Check for Python / package updates	Quarterly

8️⃣ Notes on Safety
● No “market timing” required: system works with drawdowns
● Cash management: dry powder is tracked; system will not overallocate
● Limits: Configurable per ticker to avoid overconcentration
● Logging: Always review trade_log.csv for executed orders

✅ By following this schedule, your CycleGuard system can run autonomously, keep your portfolio aligned with crash/recovery logic, and provide a visual dashboard for oversight.



If daily_rebalance.py fails to run on a day, here’s what happens and how you can handle it safely:

1️⃣ Immediate Impact
1. Portfolio State Won’t Update
    ● portfolio_state.json remains at the last recorded allocations.
    ● No trades are executed for that day, so your portfolio simply stays as-is.
2. Crash Signals Might Be Missed
    ● If the market experienced a drawdown large enough to trigger a crash level, that signal is not acted upon.
    ● This means your system misses a chance to trim risk or add cash.
3.Recovery Adjustments Won’t Occur
    ● If the market is recovering, trimming overweight positions or rebalancing cash allocations will not happen that day.
4. Trade Log Doesn’t Update
    ● trade_log.csv stays static — no record of intended trades is created.

2️⃣ Safety Considerations
    ● No trades executed = no accidental harm
        ● The system won’t misallocate or overtrade; your existing positions remain untouched.
    ● Cash / limits remain the same
        ● Dry powder and position limits are preserved.

3️⃣ How to Recover After a Missed Day
1. Run the Script Manually
    ● You can simply rerun daily_rebalance.py on the next available day.
    ● The system will catch up on any pending crash/recovery signals based on the current market drawdown.
2. Check Crash Level History
    ● rebalance_state.json keeps track of which crash levels have already been executed.
    ● The script ensures you don’t double-execute trades for the same crash level.
3. Review Trade Log
    ● Verify trade_log.csv for missed trades and confirm allocations post-run.

4️⃣ Preventing Future Failures
● Use a Scheduler / Cron Job
    ● Task Scheduler (Windows) or Cron (Linux/macOS) ensures automation.
● Add Logging & Alerts
    ● Configure the script to send an email or Slack notification if it fails.
● Monitor Daily
    ● Check Streamlit dashboard each morning to see if the previous day’s run occurred.


⚡ Key Takeaway

A missed daily run doesn’t break the portfolio, but it can delay crash/recovery responses.
    ● Portfolio remains safe, no trades are executed unintentionally.
    ● Running the script the next day will catch up automatically.


⚡ Usage
    
	

● Missed crash levels will appear in yellow / highlighted section for quick operator review.
● Dashboard updates every time you refresh or run Streamlit.





🧭 🧠 How to Read Your CycleGuard Dashboard
📊 1. Portfolio Overview
What you see:
● Ticker (FZROX, SCHD, NVDA, etc.)
● Dollar value
● % of portfolio

How to interpret:
● High % = concentration risk
	● If something like NVDA or SMH creeps too high → risk is increasing
● Cash / short-term bonds (SGOV, VUSB) = dry powder
	● This is what fuels your crash buying
	
What to do:
● Normally → do nothing
● Only act if:
	● A single position exceeds your limits (rare due to automation)

--------

📈 2. Market Data & Drawdown
What you see:
	● Current price of S&P 500 Index
	● Cycle peak
	● Drawdown (% drop from peak)

--------

🧠 This is the MOST IMPORTANT section
Example:
	Cycle Peak: 5800
	Current:    5200
	Drawdown:  -10.3%

How to interpret:
Drawdown	Meaning
0% to -10%	Normal volatility
-10%		⚠️ Level 1 trigger
-20%		🚨 Level 2 (real correction)
-30%		💥 Bear market
-40%+		🔥 Panic / capitulation

--------

What to do:

👉 You don’t decide anything manually

● The system uses this to:
	● Trigger buys during crashes
	● Trigger sells during recovery

--------

⚠️ 3. Crash Signal
What you see:
Current Crash Signal: Level 1 / Level 2 / None

--------

How to interpret:
Signal	Meaning	Action
None	Market normal	Do nothing
Level 1	Mild drop	Small deployment
Level 2	Correction	Bigger buys
Level 3	Bear market	Aggressive buying
Level 4	Panic	Maximum deployment

--------


Important:
	👉 This is NOT predictive
	👉 It is reactive and rules-based
--------

What to do:
	● If automation is running → nothing
	● If running manually → verify trades executed


⚡ 4. Missed Crash Levels
What you see:

	Level 1, Level 2

--------

How to interpret:

👉 These are levels that:

	● SHOULD have triggered earlier
	● Were executed later due to missed runs

--------

What to do:
● Just verify trades happened
● No manual correction needed


📋 5. Trade Log
What you see:
● Date
● BUY / SELL
● Asset
● Amount
● Reason (Level 1, Recovery, etc.)

--------

How to interpret:
Example:
	SELL SGOV 30000  Level 2
	BUY  FZROX 22500 Level 2

👉 Means:

● Cash was deployed
● Risk assets were bought

--------

What to look for:
✅ Trades align with crash levels
✅ No duplicate executions
✅ No unexpected assets

--------

What to do:
● Weekly review is enough
● No daily intervention required


🛠️ 6. Recovery Management
What you see:
	● Adjusted portfolio after recovery trimming

--------

How to interpret:

👉 This shows what happens when:
	● Market rebounds +20% from bottom
	● System:
		● Sells some risk assets
		● Rebuilds cash (SGOV)

--------

Why this matters:

This is how you:

👉 Avoid riding gains all the way back down

--------

What to do:
	● Usually nothing
	● Just confirm trimming is happening logically

--------

🧠 🧩 Big Picture (How It All Works Together)
Crash Phase:
	● Drawdown increases
	● System buys progressively
	● Cash → equities

--------

Bottom:
	● Max deployment
	● Portfolio most aggressive

--------

Recovery Phase:
	● Market rebounds
	● System trims risk
	● Rebuilds cash

--------

🚦 When YOU Should Actually Act
🟢 Do Nothing (most of the time)
	● Dashboard looks normal
	● Trades executing
	● Drawdown progressing logically

--------

🟡 Investigate
	● No trades during large drawdown
	● Missing data / dashboard errors
	● Portfolio not updating

--------

🔴 Intervene
	● Script not running
	● Wrong trades executed
	● Config changes needed

--------

🧠 Final Mental Model

Think of your dashboard as:

👉 An airplane cockpit
	● You’re the pilot
	● CycleGuard is the autopilot

You:
	● Monitor
	● Verify
	● Override only if necessary


Purpose of Drift Analysis

**Drift Analysis** is the "Sanity Check" of your entire CycleGuard system. It bridge the gap between what the **System** thinks you own and what you **Actually** own in your brokerage account.

In a perfect world, these two would always be identical. In the real world, they "drift" apart for several reasons.

### **The Two Sources of Truth**
1.  **System Portfolio**: This is the local data stored in `portfolio_state.json`. CycleGuard uses this to calculate rebalancing, crash protection, and recovery moves.
2.  **Fidelity Portfolio**: This is your real-world brokerage data. This is "Reality."

### **Why Does Drift Happen?**
*   **Dividends**: Your Fidelity account might automatically reinvest dividends, increasing your share count in a way CycleGuard hasn't tracked yet.
*   **Manual Trades**: If you buy or sell a stock directly in the Fidelity app without logging it in CycleGuard, the system won't know.
*   **Asset Transfers**: Moving cash or stock into or out of your account.

### **Why is Drift Analysis Important?**
1.  **Accuracy of Recommendations**: CycleGuard's rebalancing calculations (e.g., "Sell $2,000 of SMH") are only as good as the underlying data. If your system data is "drifting" by 5% or 10%, the recommendations will be incorrect.
2.  **Verification Before Syncing**: The Drift Analysis table lets you review exactly what will change *before* you click the "Sync" button. It highlights:
    *   **⚠️ Significant Drift**: Positions that are off by more than 5%.
    *   **🆕 New Positions**: Assets you bought that the system didn't know about.
    *   **❌ Missing Positions**: Assets you sold that are still lingering in your system data.
3.  **Audit Trail**: It helps you catch errors in your manual trade logging or unexpected corporate actions (like stock splits).

**In short: Drift Analysis ensures that CycleGuard is making decisions based on your actual bank account balance, not just a theoretical model!**	


The **Crash/Recovery Signals** subpanel is the command center for your strategy. It takes the raw market data (price and drawdown) and translates it into specific, actionable investment phases.

Here is how to use it and interpret what it tells you:

**1. What Information is Displayed?**

This panel shows the **Current Signal** dictated by your strategy’s "Engine." There are three primary types of signals:

● **Crash Levels** (Level 1, 2, 3, or 4): These appear during a market decline. They indicate that the S&P 500 has dropped past specific percentage milestones (e.g., -10%, -20%, -30%).
● **Recovery Signal**: This appears when the market is bouncing back from a crash and has hit your **Recovery Threshold** (e.g., 95% of the previous peak).
● **None**: This is the "All Clear" signal. It means the market is either trending normally or the drawdown isn't significant enough to warrant a move.

**2. How to Interpret the Signals**

📉 If you see a "Level" Signal (e.g., Level 1, 2, 3, 4)

● **Meaning**: The market is in a "Buy the Dip" zone.
● **Action**: This signal tells you it's time to Deploy Cash. You should check the Portfolio Recommendations below to see how much of your safe-haven asset (e.g., SGOV) you should move into your growth ETFs (e.g., SMH, SCHG).
● **Strategy**: Level 1 is a "nibble," while Level 4 is a "max deployment" during a major crash.

📈 **If you see "Recovery Triggered"**

● **Meaning**: The system believes the crash is over and the market has effectively bottomed and recovered.
● **Action**: This is time to Protect Profits. The system will recommend rotating a portion of your growth stock gains back into your safe-haven asset (SGOV).
● **Strategy**: This ensures you reload your "dry powder" (cash) so you are ready for the next market cycle.

✅ **If you see "None"**

● **Meaning**: The market is behaving within normal parameters.
● **Action: Do nothing**. Your portfolio is already in its optimal "steady state" for the current market environment.

**3. Pro Tip: Using it with the Trade Preview**

The Signal panel tells you **"What"** state the market is in. You should immediately look down at the **Trade Preview** and **Recommendations** panels to see exactly **"How Much"** you need to buy or sell to satisfy that signal.

TIP

If a signal appears, your first step should be to **Sync with Fidelity** to ensure the recommendations are based on your most recent real-world balances!


The **Trade Preview** subpanel is the most practical part of the CycleGuard dashboard. While other panels explain **"Why"** the market is crashing or **"How Much"** your portfolio has drifted, this panel tells you exactly **"What to Click"** in your brokerage account today.

Here is how to use it and interpret the information:

**1. What Information is Displayed?**

The **Trade Preview** shows a proposed list of transactions to align your real-world portfolio with the CycleGuard strategy. It typically includes:

* **Ticker**: The stock/ETF symbol (e.g., SGOV, SMH, SCHG).
* **Action**: Either BUY (in green) or SELL (in red).
* **Current Value ($)**: What you currently own in that asset.
* **Trade Amount ($)**: The dollar value of the transaction you need to place.
* **New Value ($)**: What your position total will be after the trade is complete.

**2. How to Interpret the Information**

⚖️ The "Balance" Rule
In almost all cases, the Trade Preview is Cash-Neutral. This means the total dollar amount of your SELLS will roughly equal the total dollar amount of your BUYS.

* **Interpretation**: You aren't "spending" new money or "withdrawing" cash to the bank; you are simply rotating your existing capital from "Safe" to "Growth" (or vice-versa).

🛡️ **The SGOV Rotation
Pay close attention to SGOV (or your cash-equivalent).

* **During a Crash**: You will see a large SELL recommendation for SGOV and a corresponding BUY for growth stocks. This is the system "firing" your dry powder into the market.
* **During a Recovery**: You will see a SELL for growth stocks and a BUY for SGOV. This is the system "locking in" profits.

📝 **Trade Execution**
The "Trade Amount ($)" is your **Order Size**.

* **Interpretation**: When you go to Fidelity, you would open a trade ticket, select "Dollar Amount" instead of "Shares," and type in the exact number shown in this column.

**3. Workflow Example**

1. **Check Signal: You see "Level 1" in the Signals panel.
2. View Preview: The Trade Preview shows:
	● **SELL SGOV: $5,000**
	● **BUY SMH: $2,500**
	● **BUY SCHG: $2,500**
3. **Execute**: You go to Fidelity and place those three trades.
4. **Confirm**: Once done, you come back to CycleGuard and hit the **"Confirm Trades & Log"** button in the Action panel to update your local records.

**IMPORTANT**

Always verify that your **Fidelity Sync** is fresh before following the Trade Preview! If your system data is out of date, the preview will recommend trades based on "old" values.


The **Missed Crash Levels** section is the "Catch-Up" mechanism of your strategy. Market crashes aren't always smooth; sometimes the market drops so fast (e.g., a "gap down" over a weekend) that it skips over your early price targets entirely.

Here is how to use and interpret this information:

1. **What Information is Displayed?
This panel shows a checklist of the four Crash Levels (Level 1 through Level 4).

* **"Completed"**: You successfully caught this level and logged the trade.
* **"Missed"**: The market is currently deeper than this level, but you haven't executed the trade for it yet.
* **"Pending": The market hasn't reached this depth yet.

**2. How to Interpret "Missed" Levels
🏃 The "Catch-Up" Logic
If you see one or more levels marked as "Missed," don't panic. CycleGuard is designed to be "Aggressive on Gaps."

* **Interpretation**: The system will automatically **Add Up the dollar amounts of all missed levels and include them in your current **Trade Preview.
NOTE

Example: If Level 1 requires a $5,000 buy and Level 2 requires a $5,000 buy, and you were away on vacation when both hit—the system will show a single $10,000 BUY recommendation today.

⏱️ **Timing is Everything**

* **Interpretation**: If you see a missed level, it means the market is currently "cheaper" than your original target. The system is telling you to execute the trade now to stay on schedule with your total capital deployment plan.

**3. Why This Matters for Your Strategy**
The goal of CycleGuard is to ensure a specific percentage of your cash is moved into the market at specific crash depths.

* **If you skip a level**: You would end up under-exposed when the recovery starts.
* **The Solution**: This panel ensures that no matter when you open the dashboard, you are always given a recommendation that brings your portfolio up to the **Exact Exposure Level** required for the current market drawdown.

**In short: If you see "Missed" levels, simply follow the Trade Preview below—it has already done the math to "bundle" your missing trades into one easy transaction!**



The **Recovery State** subpanel is the final stage of your market cycle. Where the "Missed Crash Levels" panel focuses on **Buying the Dip**, the Recovery State subpanel focuses on **Locking in Gains** as the market returns to its previous high.

Here is how to use and interpret this information:

**1. What Information is Displayed?**

This panel tracks the state of your "Profit Rotation" mechanism. It typically includes:

* **Recovery Threshold**: This is your target (default 95%). It means "Once the market is within 5% of its previous all-time high, I want to take profits."
* **Current State**:
    * **"Crashed"**: The system is waiting for the market to bounce back. No recovery moves yet.
    * **"Triggered"**: The market has successfully hit your threshold. Profit rotation is now active.
    * **"Complete"**: You have already rotated your profits for this cycle and are back in your "Safe Mode."
* **Rotation Log**: A simple list showing if you have already rebalanced your Growth (SMH/SCHG) stocks back into Cash (SGOV) for this recovery cycle.

**2. How to Interpret the State**

🎯 **"Triggered" (The Selling Signal)**

* **Interpretation**: This is the most exciting state! It means your "Buy the Dip" strategy worked, the market has recovered, and it's time to cash out your extra growth shares.
* **Strategy**: This is when the **Trade Preview** will recommend **SELLING** your winners (SMH, SCHG) and **BUYING** your cash-haven (SGOV).

⏳ **"Crashed" (The Waiting Game)**
* **Interpretation**: The market is still in a drawdown. CycleGuard is keeping your money in Growth Stocks to catch the full bounce-back.
* **Strategy**: No actions required here except patience.

✅ **"Complete" (The Reset)**

* **Interpretation**: You have successfully executed your rotation. You are now back to your "Base" portfolio (e.g., 60% Cash, 40% Growth).
* **Strategy**: You are now perfectly positioned with "Dry Powder" (cash) to wait for the next market crash.

**3. Why This Matters for Your Strategy**

Most investors fail because they buy during a crash but **forget** to sell during the recovery, leading them to be over-exposed when the next crash happens.

This panel provides the **Discipline** to take your winnings off the table and move them back to a safe asset like SGOV. This ensures that the profit from one market cycle is locked in and ready to be used to "Buy the Dip" in the next one.

**In short: When this panel says "Triggered," it’s your signal to take chips off the table and prepare for the next cycle!**


The **Executed Trades** subpanel is your portfolio's "Strategic Memory." It provides a historical audit trail of every move that CycleGuard has recommended and that you have confirmed.

Here is how to use it and interpret your past performance:

**1. What Information is Displayed?**

This panel is an interactive table showing the contents of your trade_log.csv. It typically displays:

* **Date**: The exact timestamp when you clicked "Confirm Trades" in the dashboard.
* **Symbol**: The stock/ETF traded (e.g., SMH, SGOV, SCHG).
* **Action**: Whether it was a BUY or SELL.
* **Amount ($)**: The dollar value of the trade at the time it occurred.
* **Signal Type**: The reason for the trade (e.g., "Crash Level 1" or "Recovery Rotation").



**2. How to Interpret the History**

🕰️ Seeing the Strategy in Motion
If you scroll back through your history, you should see distinct "Cycles" appearing:

* **During Crashes:** You will see a cluster of BUY entries for growth stocks (SMH, SCHG). This proves you were buying when everyone else was fearful.
* **During Recoveries:** You will see a cluster of SELL entries for those same stocks. This proves you were taking profits when the market felt "safe" again.

📊 **Auditing Your Deployment**

* **Interpretation:** If you see multiple "BUY" entries for SMH but only one "SELL" entry, it means you are currently in a deployed state and catching the ride back up.
* **Strategy:** If the market is at a new all-time high but you don't see any "Recovery Rotation" trades in your log, you might have forgotten to hit the confirm button after your last recovery move!

📑 **Tax & Review**

* **Interpretation:** This table is a quick "Cheat Sheet" for your tax year. While you should always use your official Fidelity 1099 for taxes, this log tells you exactly which months were your most active from a strategic rotation standpoint.

**3. Why This Matters for Your Strategy**
The Executed Trades panel creates **Confidence**. Following a strategy like CycleGuard requires discipline during scary market drops. Looking back at this log and seeing "BUY SMH: -$10,000" during a 20% crash—and then seeing the market higher today—is a powerful psychological tool to help you stay the course during the next crash.

**In short: This isn't just a receipt list—it’s a visual representation of your discipline and your ability to "Buy Low and Sell High" systematically!**

1















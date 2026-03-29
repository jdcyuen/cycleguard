






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

● This will:
1. Fetch latest S&P 500 / market data
2. Calculate drawdown and check crash signals
3. Execute trades if needed
4. Update portfolio state (portfolio_state.json)
5. Update trade log (trade_log.csv)
6. Apply recovery trims if conditions are met

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
    streamlit run src/dashboard/cycleguard_dashboard.py

● Missed crash levels will appear in yellow / highlighted section for quick operator review.
● Dashboard updates every time you refresh or run Streamlit.



#Run tests via:
python -m unittest tests/test_crash_manager.py
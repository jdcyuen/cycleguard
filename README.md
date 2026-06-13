
E:\CycleGuard

Github repository
https://github.com/jdcyuen/cycleguard.git

If you are just running the code locally on your machine, you don't have to do anything. It will automatically default to dev and use dev.yaml.

If you want to run your tests, your test suite (or you) can set the environment variable right before running the code so it uses test.yaml:

powershell
-----------
$env:CYCLEGUARD_ENV="test"
pytest

If you are deploying to production, you would configure your server/host to have the environment variable set to prod, and it will automatically switch to using prod.yaml.


How to run:

    cd E:\CycleGuard
    python scripts\daily_rebalance.py
or
	streamlit run src/dashboard/cycleguard_dashboard.py


#Run tests via:
python -m unittest tests/test_crash_manager.py

#To run the ingestion pipline cli

To run the command line for the CycleGuard portfolio ingestion pipeline, you should run it as a Python module from the project root (E:\CycleGuard).

The Run Command
bash
python -m src.cli.ingest_positions --file <path_to_csv> [options]


Command Line Arguments
--file (Required): The path to your portfolio CSV file.
--snapshot-date (Optional): An explicit date to associate with the snapshot in YYYY-MM-DD format.
--confirm (Optional): A flag to bypass the interactive Proceed with ingestion? (y/n) confirmation prompt.

Ingestion Date Resolution
If you do not explicitly provide a --snapshot-date argument, the CLI resolves the date automatically using the following order of priority:

1. Filename Parsing: It attempts to extract a date from the file name if it matches the pattern Portfolio_Positions_Month_Day_Year.csv (e.g. Portfolio_Positions_Jan_15_2026.csv resolves to 2026-01-15).

2. Fallback: If no date pattern is found in the filename, it defaults to the current date.

    Examples
        1. Standard manual run (will prompt for confirmation):

        powershell
        python -m src.cli.ingest_positions --file "Portfolio_Positions_Jan_15_2026.csv"

        2. Automated run with explicit date and confirmation bypass:

        powershell
        python -m src.cli.ingest_positions --file "my_positions.csv" --snapshot-date "2026-05-28" --confirm



To access the database via the command line:

    psql -h localhost -p 5433 -U postgres -d cycleguard


To access the database via psql, you need to use the -U flag to specify the username, -d to specify the database name, and -p to specify the port number.

Password: When prompted, enter Nokia*90.
Useful commands once connected:
List all tables: \dt
Inspect table schema (e.g., positions): \d positions
Run a query: SELECT * FROM snapshots;
Exit: \q




To obtain all portfolio information for a single ticker, you need to perform an SQL JOIN between the tables in your database (positions, securities, snapshots, and accounts).

Here is the perfect query to do that. Copy and paste this into your psql terminal (replacing 'MU' with whatever ticker you want to query, e.g., 'SMH', 'AAPL', etc.):

SELECT 
    s.snapshot_date,
    a.account_name,
    sec.ticker,
    sec.description,
    p.quantity,
    p.avg_cost,
    p.market_value,
    p.total_gain,
    p.total_gain_pct
FROM positions p
JOIN securities sec ON p.security_id = sec.id
JOIN snapshots s ON p.snapshot_id = s.id
JOIN accounts a ON p.account_id = a.id
WHERE sec.ticker = 'MU';
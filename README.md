
E:\CycleGuard

Github repository
https://github.com/jdcyuen/cycleguard.git

##Environment

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

#To run the ingestion pipline cli for positions:

To run the command line for the CycleGuard portfolio ingestion pipeline, you should run it as a Python module from the project root (E:\CycleGuard).

##Ingestion command line for positions
The Run Command
bash
python -m src.cli.ingest_positions --file <path_to_csv> [options]

Example:

    python -m src.cli.ingest_positions --file "C:\Users\Joe\Downloads\Portfolio_Positions_Jan_15_2026.csv" --account rollover_ira --snapshot-date 2026-01-15 --confirm


Command Line Arguments
--file (Required): The path to your portfolio CSV file.
--snapshot-date (Optional): An explicit date to associate with the snapshot in YYYY-MM-DD format.
--confirm (Optional): A flag to bypass the interactive Proceed with ingestion? (y/n) confirmation prompt.

--account (Optional): The name of the account to import the positions into. If not provided, the CLI will prompt the user to select an account.

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

    

##Ingestion command line for transactions

#To run the ingestion pipline cli for transactions:

To run the command line for the CycleGuard transaction ingestion pipeline, you should run it as a Python module from the project root (E:\CycleGuard).



Example:


python -m src.cli.ingest_transactions --file "K:\Joe\Fidelity\2026\Rollover\Transactions\Apr2026.csv" --account rollover_ira --confirm


Command Line Arguments
--file (Required): The path to your transactions CSV file.
--account (Optional): The name of the account to import the transactions into. If not provided, the CLI will prompt the user to select an account.
--confirm (Optional): A flag to bypass the interactive Proceed with ingestion? (y/n) confirmation prompt.




##Database


To access the database via the command line:

    psql -h localhost -p 5433 -U postgres -d cycleguard


To access the database via psql, you need to use the -U flag to specify the username, -d to specify the database name, and -p to specify the port number.

Password: When prompted, enter Nokia*90.
Useful commands once connected:
List all tables: \dt
Inspect table schema (e.g., positions): \d positions
Run a query: SELECT * FROM snapshots;
Exit: \q

psql -p 5433 -U cycleguard_user -d cycleguard
Password: When prompted, enter Wilhelmina1364Rise


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




In PostgreSQL, there are two common ways to clear a table.

Option 1: Delete all rows

    DELETE FROM cycleguard.transactions;

or

    DELETE FROM cycleguard.positions;

Pros

    Preserves table structure.
    Can be rolled back if inside a transaction.

Cons

    Slower for large tables.
    Does not reset SERIAL/identity sequences.


Option 2: Truncate table (recommended for imports)

    TRUNCATE TABLE cycleguard.transactions;

or

    TRUNCATE TABLE cycleguard.positions;

Pros

    Very fast.
    Removes all rows instantly.

Cons

    Requires appropriate permissions.
    Doesn't reset sequences unless requested.

Reset IDs back to 1

If you want the next inserted row to start at ID 1 again:

    TRUNCATE TABLE cycleguard.transactions
    RESTART IDENTITY;

or

    TRUNCATE TABLE cycleguard.positions
    RESTART IDENTITY;


Clear multiple related tables

If foreign keys exist between tables:

    TRUNCATE TABLE
            cycleguard.positions,
            cycleguard.securities,
            cycleguard.accounts,
            cycleguard.snapshots,
            cycleguard.transactions,
            cycleguard.import_history
    RESTART IDENTITY CASCADE;



The CASCADE tells PostgreSQL to also truncate dependent tables.

See row counts before clearing

    SELECT COUNT(*) FROM cycleguard.positions;
    SELECT COUNT(*) FROM cycleguard.transactions;
    SELECT COUNT(*) FROM cycleguard.import_history;


For a full CycleGuard reset




If you want to completely reload positions and transactions from scratch:

    TRUNCATE TABLE
        cycleguard.positions,
        cycleguard.transactions,
        cycleguard.snapshots,
        cycleguard.import_history,
        cycleguard.accounts,
        cycleguard.securities
    RESTART IDENTITY CASCADE;

This keeps your tables, indexes, constraints, accounts, and securities intact, while removing all imported data.

Add unique constraint:

ALTER TABLE cycleguard.snapshots
ADD CONSTRAINT uq_snapshot
UNIQUE (
    id,
    snapshot_date
);

This guarantees the database cannot contain duplicate snapshots.



##Cycleguard Architecture


##Testing    

Running Unit tests:
pytest tests/repositories/test_account_repository.py -vv
pytest tests/repositories/test_import_history_repository.py -vv
pytest tests/repositories/test_positions_repository.py -vv
pytest tests/repositories/test_security_repository.py -vv
pytest tests/repositories/test_snapshot_repository.py -vv
pytest tests/repositories/test_transaction_repository.py -vv

pytest tests/config/test_schema_validator.py -vv
pytest tests/config/test_config_manager.py -vv
pytest tests/config/test_config_loader.py -vv
pytest tests/ingestion/common/test_cli_ingestion_helper.py -vv
pytest tests/services/test_positions_ingestion_service.py -vv











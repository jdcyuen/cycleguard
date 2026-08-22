# Local Project path
    * E:\CycleGuard

# Github repository
    * https://github.com/jdcyuen/cycleguard.git

# CycleGuard Project Documentation
    * https://github.com/jdcyuen/cycleguard/blob/main/docs/system_design.md


---


CycleGuard is a portfolio management and risk-control system designed to help manage an investment portfolio through changing market and economic conditions.

Its core purpose is to answer three questions:

1. What do I own?
    * Accounts
    * Positions
    * Transactions
    * Cash
    * Asset classes and portfolio buckets
2. What is happening in the market?
    * Price trends
    * Market breadth
    * Volatility
    * Interest rates and bond yields
    * Credit conditions
    * Technical indicators
    * Economic/market regime
3. What should I do about it?
    * Compare current holdings with target allocations
    * Detect excessive drift or concentration
    * Identify changes in market regime
    * Generate buy/sell/rebalance recommendations
    * Control portfolio risk
    * Provide a disciplined, rules-based response rather than relying on emotion


# CycleGuard

CycleGuard is a rules-based portfolio management and risk-control engine that integrates portfolio data, market conditions, and investment rules to determine how a portfolio should be positioned as market conditions change.

The important architectural idea is that CycleGuard is not simply a portfolio tracker. It is intended to evolve from an accurate record of the portfolio into a system that analyzes risk and market conditions and recommends—or eventually executes—portfolio actions.

## CycleGuard Ingestion Pipeline

The CycleGuard ingestion pipeline is the process by which transaction and position data is imported from Fidelity into the CycleGuard database. The ingestion pipeline is a multi-step process that includes loading the CSV data, validating the data, resolving the account, recording the import, and persisting the data to the database.

The ingestion pipeline is invoked through the CycleGuard CLI, which provides a user interface for importing transaction and position data from Fidelity.

The ingestion pipeline is the process that takes investment data downloaded from Fidelity as CSV files and converts it into structured, validated CycleGuard data.

Its job is to move data from the external source—Fidelity—into the CycleGuard database while maintaining traceability and transactional integrity.

At a high level:

```python

Fidelity
   │
   │ CSV file
   ▼
┌──────────────────────┐
│   Ingestion Pipeline │
└──────────┬───────────┘
           │
           ▼
      Load the file
           │
           ▼
      Validate data
           │
           ▼
      Resolve account
           │
           ▼
      Record import
           │
           ▼
       Persist data
           │
           ├──────────────┐
           ▼              ▼
     Transactions     Positions
                           │
                           ▼
                       Snapshot
           │
           ▼
       Audit import
           │
           ▼
        COMMIT

```
---

The ingestion pipeline can import both transactions and positions. The flow is almost identical, with two key differences:

| Transactions | Positions |
|--------------|-----------|
| Creates transactions records | Creates position records |
| Updates positions to current state | Creates a snapshot record |
| Updates aggregated tables (e.g., weekly balances) | Does not create aggregated tables |

In both cases, the goal is to preserve the fidelity of the imported data while maintaining the strict rules CycleGuard enforces (like disallowing negative cash balances).

---

### 1. Fidelity provides the source data

The process begins outside CycleGuard.

The user downloads a CSV file from Fidelity, such as:

Fidelity_Positions.csv
Fidelity_Transactions.csv

These files are the source records for the import.

CycleGuard does not directly connect to Fidelity. Instead, the downloaded CSV is supplied to the appropriate CycleGuard ingestion CLI.

For example:

python -m cli.ingest_transactions --file transactions.csv

or:

python -m cli.ingest_positions --file positions.csv


---

### 2. The CLI starts the ingestion

The CLI is the entry point into the pipeline.

Its responsibility is primarily to:

receive the filename
receive account information
parse command-line options
construct the appropriate ingestion service
invoke the service
display the result

The CLI does not perform the actual import logic.

Conceptually:

```python
User
 │
 ▼
CLI
 │
 │ service.ingest(...)
 ▼
Ingestion Service

```
---

### 3. The loader reads the CSV

The ingestion service passes the CSV file to the loader.

The loader is responsible for converting the external CSV representation into objects that CycleGuard can work with.

```python
Fidelity CSV
     │
     ▼
   Loader
     │
     ▼
CycleGuard data objects
```
---

### 4. The validator validates the data

The loaded data is then passed to the validator.

The validator checks that the data is structurally and logically acceptable before CycleGuard modifies the database.

```python
Loaded data
     │
     ▼
 Validator
     │
     ├── valid ───────► continue
     │
     └── invalid ─────► exception

```

This is an important safety boundary:

Invalid input should not result in partially imported portfolio data.

---

### 5. CycleGuard resolves the account

The pipeline determines which CycleGuard account the Fidelity data belongs to.

For example:

```python
Fidelity
    │
    ▼
"Rollover IRA"
    │
    ▼
accounts.id = 1

```

The database account ID is then used by the records created during the import.

---

###  6. The import is recorded

Before the actual portfolio records are persisted, CycleGuard creates an import_history record.

For example:

```python
Import History
──────────────────────────────
ID:             123
Account:        Rollover IRA
Import Type:    positions
Institution:    Fidelity
Filename:       Fidelity_Positions.csv
File Hash:      84e958...
Snapshot Date:  2026-08-22
Status:         RUNNING
```

The import_history_id becomes the identifier connecting the data created by this import to its source.

This is a key part of CycleGuard's auditability.

---

### 7. The data is persisted

The ingestion service then calls the appropriate persistence logic.

For a transaction import:

```python
Fidelity Transactions CSV
             │
             ▼
       Transactions
             │
             ▼
      transactions table
```

For a positions import:

```python
Fidelity Positions CSV
             │
             ▼
          Positions
             │
             ├──────────────► positions table
             │
             └──────────────► Snapshot
                                  │
                                  ▼
                             snapshots table

```

The records contain the import_history_id.

For example:

```python
transactions
────────────────────────
id
account_id
import_history_id
...
```

and:

```python
positions
────────────────────────
id
account_id
import_history_id
...
```

and:

```python
snapshots
────────────────────────
id
account_id
import_history_id
...
```

---
### 8. TransactionManager controls the database transaction

This is an important distinction in the architecture.

The ingestion service performs the business workflow, but the TransactionManager controls whether the database changes are committed or rolled back.

Conceptually:

```python
TransactionManager
        │
        ▼
      BEGIN
        │
        ├── import_history
        ├── transactions / positions
        ├── snapshots
        └── update import_history
        │
        ├── success ──► COMMIT
        │
        └── exception ─► ROLLBACK

```
If an exception occurs during the import, the database transaction is rolled back.

That means CycleGuard does not intentionally leave half an import committed.

---
### 9. Import history is completed

If persistence succeeds, the import history record is updated.

For example:

```python
Import History
──────────────────────────────
ID:             123
Status:         SUCCESS
Rows Read:      500
Rows Imported:  487
Rows Skipped:    13
```
If the import fails, it should instead record the appropriate failure information.

The important point is that import history provides the audit trail for the ingestion operation.

---

### 10. The import is audited

Your current architecture also performs an import audit after persistence.

Conceptually:

```python
Persist
   │
   ▼
Import Audit
   │
   ├── PASS ──► import can complete
   │
   └── FAIL ──► import fails

```
This gives CycleGuard another layer of protection.

The import isn't considered successfully completed simply because the database accepted the rows. The resulting data must also pass the application's audit checks.

---

### 11. Commit or rollback

If all validations succeed, the transaction is committed.

If any validation fails, the transaction is rolled back, and the database is returned to the state it was in before the import started.

Conceptually:

```python
Database transaction
─────────────────────────────
BEGIN
  │
  ├── INSERT import_history
  ├── INSERT transactions / positions
  ├── INSERT snapshots (positions only)
  ├── UPDATE import_history
  │
  ├── Commit → Success
  │
  └── Rollback → Failure

```
This is an atomic operation from the perspective of the database. Either the entire import succeeds, or the entire import is rolled back.

---

### 12. Success is reported

The final step is to report success to the user.

Conceptually:

```python
CLI → Success message

```
---
## What happens when something goes wrong?

There are two different situations that are important to distinguish.

##### :one:. Failure during the database transaction

The TransactionManager handles this:

```python
ROLLBACK
```
The uncommitted database changes are removed.

The ingestion service does not call ImportRollbackService.

##### :two:. Manual cleanup of a committed import

A different situation is:

```python
Import
  ↓
COMMIT
  ↓
Later discover import was wrong

```
The data is now legitimately committed.

The operator can explicitly run:

```python
python -m cli.rollback_import --import-history-id 123
```
which invokes:

```python
ImportRollbackService
```
and removes the data associated with that import.

By default, the import_history record remains so there is an audit trail of what happened.

---

### 13. The ingestion pipeline is designed for traceability and correctness.

* **Import history** traces each import to a specific CSV file.

* **Data validation** ensures that the data is correct before it enters the database.

* **Transaction management** ensures that the database is always in a valid state.

* **Audit checks** verify that the imported data is correct.

---

This design makes CycleGuard imports auditable, reliable, and safe to run.

### The complete pipeline
```python
                       FIDELITY
                          │
                          │ CSV
                          ▼
                     ┌─────────┐
                     │   CLI   │
                     └────┬────┘
                          │
                          ▼
                ┌───────────────────┐
                │ Ingestion Service │
                └─────────┬─────────┘
                          │
              ┌───────────┼───────────┐
              ▼           ▼           ▼
           Loader     Validator    Account
              │           │        Resolve
              └───────────┼───────────┘
                          │
                          ▼
                   Import History
                     RUNNING
                          │
                          ▼
                    Persistence
                          │
              ┌───────────┴───────────┐
              ▼                       ▼
        Transactions              Positions
                                      │
                                      ▼
                                  Snapshot
              │                       │
              └───────────┬───────────┘
                          ▼
                     Import Audit
                          │
                     ┌────┴────┐
                     │         │
                    PASS      FAIL
                     │         │
                     ▼         ▼
                  SUCCESS   Exception
                     │         │
                     ▼         ▼
                   COMMIT   ROLLBACK
```
The fundamental design principle is:

>The ingestion pipeline is responsible for safely transforming Fidelity CSV data into trusted CycleGuard data. The TransactionManager guarantees database atomicity, while Import History provides traceability and the rollback service provides deliberate manual cleanup of committed imports.

This makes ingestion the foundation of CycleGuard: everything that comes later—portfolio aggregation, bucket mapping, market analysis, regime classification, risk scoring, and rebalancing—depends on this pipeline producing accurate and auditable portfolio data.


---

## Positions

In CycleGuard, a position represents a security that is currently held in an investment account. A position describes what the account owns, rather than an individual transaction that occurred in the account.

The source of position data is a Fidelity positions CSV file downloaded by the user. The file contains Fidelity's representation of the securities currently held in the account, including information such as the security symbol, quantity, price, and market value.

The position data enters CycleGuard through the ingestion pipeline:

```python
Fidelity
   │
   │ Positions CSV
   ▼
Ingestion Pipeline
   │
   ├── Load CSV
   ├── Validate data
   ├── Resolve account
   ├── Record import
   └── Persist positions
           │
           ▼
      Positions Table
```

Once imported, the positions are stored in CycleGuard's positions table. They become the system's structured representation of the holdings reported by Fidelity.

---

## Transactions

In CycleGuard, a transaction represents a financial event or activity that occurred in an investment account. Unlike a position, which describes what the account currently holds, a transaction describes something that happened to the account.

The source of transaction data is a Fidelity transaction CSV file downloaded by the user. The file contains Fidelity's record of account activity, such as purchases, sales, dividends, interest, transfers, and other cash or security movements.

The transaction data enters CycleGuard through the ingestion pipeline:

```python
Fidelity
   │
   │ Transactions CSV
   ▼
Ingestion Pipeline
   │
   ├── Load CSV
   ├── Validate data
   ├── Resolve account
   ├── Record import
   └── Persist transactions
           │
           ▼
     Transactions Table

```
---
## Snapshots

In CycleGuard, a snapshot represents the state of an investment account's holdings at a specific point in time. It provides a historical record of what the account looked like at that time, including the positions and their values.

Unlike a transaction, which represents an individual event, a snapshot represents a point-in-time state of the account.

The source of snapshot data is the Fidelity positions CSV file downloaded by the user. When a positions file is imported, the information reported by Fidelity can be used to create a snapshot of the account for the applicable snapshot date.

The snapshot fits into the ingestion pipeline as follows:

```python
Fidelity
   │
   │ Positions CSV
   ▼
Ingestion Pipeline
   │
   ├── Load CSV
   ├── Validate data
   ├── Resolve account
   ├── Record import
   │
   ├── Persist positions
   │
   └── Create snapshot
           │
           ▼
      Snapshots Table
```

---

## CLI
From the cli, you can import positions and transactions into the database. From your Fidelity account, you can download transaction and position history from your account. Run these commands from the project root directory: E:\CycleGuard


For positions

Usage: `python -m src.cli.ingest_positions --file <path_to_csv> --account <account_name> --snapshot-date <snapshot_date> --dry-run --confirm`

Command Line Arguments
* --file (Required): The path to your portfolio CSV file.
* --snapshot-date (Optional): An explicit date to associate with the snapshot in YYYY-MM-DD format.
* --dry-run (Optional): A flag to run the command without making any changes to the database.
* --confirm (Optional): A flag to bypass the interactive Proceed with ingestion? (y/n) confirmation prompt.

Example:

```bash
    python -m src.cli.ingest_positions --file "C:\Users\Joe\Downloads\Portfolio_Positions_Jan_15_2026.csv" --account rollover_ira --snapshot-date 2026-01-15
```


For transactions:

Usage: `python -m src.cli.ingest_transactions --file <path_to_csv> --account <account_name> --dry-run --confirm`

Example:

```bash
python -m src.cli.ingest_transactions --file "K:\Joe\Fidelity\2026\Rollover\Transactions\Apr2026.csv" --account rollover_ira --confirm

Command Line Arguments
* --file (Required): The path to your transactions CSV file.
* --account (Optional): The name of the account to import the transactions into. If not provided, the CLI will prompt the user to select an account.
* --dry-run (Optional): A flag to run the command without making any changes to the database.
* --confirm (Optional): A flag to bypass the interactive Proceed with ingestion? (y/n) confirmation prompt.

Example:

```bash
    python -m src.cli.ingest_transactions --file "C:\Users\Joe\Downloads\Portfolio_Transactions_Jan_15_2026.csv" --account rollover_ira --snapshot-date 2026-01-15
```

For import rollback:

Usage: `python -m src.cli.rollback_import --import-history-id <IMPORT_HISTORY_ID> --confirm --delete-import-history`

Command Line Arguments
* --import-history-id (Required): The ID of the import history to roll back.
* --confirm (Optional): A flag to bypass the interactive Are you sure? (y/n) confirmation prompt.
* --delete-import-history (Optional): A flag to delete the import history after rolling back.

Example:

```bash
    python -m src.cli.rollback_import --import-history-id 123 --confirm --delete-import-history
```

## Other cli programs
* daily_rebalance.py:
    * `python scripts\daily_rebalance.py`

* debug_csv.py:
    * `python scripts\debug_csv.py`

* get_ohlc.py:
    * `python scripts\get_ohlc.py`

* sync_portfolio.py:
    * `python scripts\sync_portfolio.py`

* technical_indicators.py:
    * `python scripts\technical_indicators.py` symbol for ticker --period for history length --interval for price data (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, all, max)

    examples:
    * `python scripts\technical_indicators.py SPMO`
    * `python scripts\technical_indicators.py SPMO --period 6mo --interval 1d`
    * `python scripts\technical_indicators.py SPMO --period 6mo --interval 1d --export`
```

---

##Environment

If you are just running the code locally on your machine, you don't have to do anything. It will automatically default to dev and use dev.yaml.

If you want to run your tests, your test suite (or you) can set the environment variable right before running the code so it uses test.yaml:

powershell
-----------
```bash
C:\Users\Joe>powershell
Windows PowerShell
Copyright (C) Microsoft Corporation. All rights reserved.

Try the new cross-platform PowerShell https://aka.ms/pscore6

PS C:\Users\Joe>

```

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
* --file (Required): The path to your portfolio CSV file.
* --snapshot-date (Optional): An explicit date to associate with the snapshot in YYYY-MM-DD format.
* --confirm (Optional): A flag to bypass the interactive Proceed with ingestion? (y/n) confirmation prompt.
* --account (Optional): The name of the account to import the positions into. If not provided, the CLI will prompt the user to select an account.

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
* --file (Required): The path to your transactions CSV file.
* --account (Optional): The name of the account to import the transactions into. If not provided, the CLI will prompt the user to select an account.
* --confirm (Optional): A flag to bypass the interactive Proceed with ingestion? (y/n) confirmation prompt.


---



## Database


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

---

##Cycleguard Architecture

---
##Testing    

Running Unit tests:
pytest -x tests/repositories/test_account_repository.py -vv
pytest -x tests/repositories/test_import_history_repository.py -vv
pytest -x tests/repositories/test_positions_repository.py -vv
pytest -x tests/repositories/test_security_repository.py -vv
pytest -x tests/repositories/test_snapshot_repository.py -vv
pytest -x tests/repositories/test_transaction_repository.py -vv

pytest -x tests/config/test_schema_validator.py -vv
pytest -x tests/config/test_config_manager.py -vv
pytest -x tests/config/test_config_loader.py -vv
pytest -x tests/ingestion/common/test_cli_ingestion_helper.py -vv
pytest -x tests/services/test_positions_ingestion_service.py -vv
pytest -x tests/services/test_transactions_ingestion_service.py -vv
pytest -x tests/services/test_import_rollback_service.py -vv
pytest -x tests/services/test_import_audit_service.py -vv

pytest -x tests/services/test_base_ingestion_service.py -vv

---





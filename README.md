# Local Project path
    E:\CycleGuard

# Github repository
    https://github.com/jdcyuen/cycleguard.git

# CycleGuard Project Documentation
    https://github.com/jdcyuen/cycleguard/blob/main/docs/system_design.md


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

## Table of Contents

- [1. Ingestion Pipeline](#1-ingestion-pipeline)
    - [1.1. Fidelity provides the source data](#11-fidelity-provides-the-source-data)
    - [1.2. The CLI starts the ingestion](#12-the-cli-starts-the-ingestion)
    - [1.3. Supported Inputs](#13-supported-inputs)
    - [1.4. The Ingestion Pipeline's Structure](#14-the-ingestion-pipelines-structure)
    - [1.5. Validation](#15-validation)

    - [1.6. Record Import](#16-record-import)
    - [1.7. Finalizing Persistence](#17-finalizing-persistence)
    - [1.8. The import_history Table](#18-the-import_history-table)
    - [1.9. Snapshotting](#19-snapshotting)
    - [1.10. Transaction Logic](#110-transaction-logic)
    - [1.11. Rollback](#111-rollback)
        - [1.11.1 The Rollback Strategy](#1111-the-rollback-strategy)
        - [1.11.2 Why Rollback Exists](#1112-why-rollback-exists)
        - [1.11.3 How Rollback Works](#1113-how-rollback-works)
        - [1.11.4 CLI](#1114-cli)
- [2. Bucket Mapper](#2-bucket-mapper)
- [3. Portfolio Aggregation Engine](#3-portfolio-aggregation-engine)
    - [3.1 What is the Portfolio Aggregation Engine?](#31-what-is-the-portfolio-aggregation-engine)
    - [3.2 The architecture](#32-the-architecture)
    - [3.3 The three main inputs](#33-the-three-main-inputs)
        - [3.3.1 PositionRepository](#331-positionrepository)
        - [3.3.2 AccountConfig](#332-accountconfig)
        - [3.3.3 The service sits between them](#333-the-service-sits-between-them)
    - [3.4 First layer: retrieve positions](#34-first-layer-retrieve-positions)
    - [3.5 Second layer: map positions into buckets](#35-second-layer-map-positions-into-buckets)
    - [3.6 Third layer: calculate values](#36-third-layer-calculate-values)
    - [3.7 Fourth layer: calculate actual weights](#37-fourth-layer-calculate-actual-weights)
    - [3.8 Fifth layer: obtain target weights](#38-fifth-layer-obtain-target-weights)
    - [3.9 Sixth layer: calculate drift](#39-sixth-layer-calculate-drift)
    - [3.10 The BucketAllocation model](#310-the-bucketallocation-model)
    - [3.11 Position allocation is another level](#311-position-allocation-is-another-level)
    - [3.12 The top-level PortfolioAllocation](#312-the-top-level-portfolioallocation)
    - [3.13 Why this architecture is useful](#313-why-this-architecture-is-useful)
    - [3.14 What the engine does NOT do](#314-what-the-engine-does-not-do)
    - [3.15 The complete Portfolio Aggregation flow](#315-the-complete-portfolio-aggregation-flow)

- [4. Market Regime Engine](#4-market-regime-engine)
    - [4.1. Market Regime Engine Architecture](#41-market-regime-engine-architecture)
        - [4.1.1 Purpose](#411-purpose)
        - [4.1.2 Where It Fits in CycleGuard](#412-where-it-fits-in-cycleguard)
        - [4.1.3 High-Level Architecture](#413-high-level-architecture)
        - [4.1.4 RegimeEngine Class](#414-regimeengine-class)
        - [4.1.5 SignalFactory Class](#415-signalfactory-class)
        - [4.1.6 SignalAggregator](#416-signalaggregator)
        - [4.1.7 The Six Market Signals](#417-the-six-market-signals)
            - [4.1.7.1 Trend Signal](#4171-trend-signal)
            - [4.1.7.2 Breadth Signal](#4172-breadth-signal)
            - [4.1.7.3 Volatility Signal](#4173-volatility-signal)
            - [4.1.7.4 Leadership Signal](#4174-leadership-signal)
            - [4.1.7.5 Credit Signal](#4175-credit-signal)
            - [4.1.7.6 Cape Signal](#4176-cape-signal)
        - [4.1.8 Regime Classifier](#418-regime-classifier)
        - [4.1.9 Configuration-Driven Classification](#419-configuration-driven-classification)
        - [4.1.10 All Conditions Must Match](#4110-all-conditions-must-match)
        - [4.1.11 Configuration Order Matters](#4111-configuration-order-matters)
        - [4.1.12 TRANSITION Is the Safety Net](#4112-transition-is-the-safety-net)
        - [4.1.13 Data Flow](#4113-data-flow)
        - [4.1.13.1  Example of Data Flow](#41131-example-of-data-flow)
        - [4.1.14 Why This Architecture Is Valuable](#4114-why-this-architecture-is-valuable)
        - [4.1.15  Relationship to the Portfolio Engine](#4115-relationship-to-the-portfolio-engine)
        - [4.1.16 Architectural Principle](#4116-architectural-principle)
- [5. Deployment Engine](#5-deployment-engine)
    - [5.1 Purpose](#51-purpose)
    - [5.2 Where the Deployment Engine Fits](#52-where-the-deployment-engine-fits)
    - [5.3 Deployment vs. Trading](#53-deployment-vs-trading)
    - [5.4 Core Responsibility](#54-core-responsibility)
    - [5.5 How the Deployment Engine Works](#55-how-the-deployment-engine-works)
    - [5.6 Deployment Strategies](#56-deployment-strategies)
    - [5.6.1 Regime-Based Deployment](#561-regime-based-deployment)
    - [5.6.2 Crash-Based Deployment](#562-crash-based-deployment)
    - [5.7 Crash Deployment](#57-crash-deployment)
    - [5.8 Drawdown Detection](#58-drawdown-detection)
        - [5.8.1 Drawdown Calculation](#581-drawdown-calculation)
        - [5.8.2 Crash Levels](#582-crash-levels)
        - [5.8.3 Crash Deployment Levels](#583-crash-deployment-levels)
    - [5.9 Cash Is a Deployment Resource](#59-cash-is-a-deployment-resource)
    - [5.10 Cash Deployment Policy](#510-cash-deployment-policy)
    - [5.11 Deployment Engine Does Not Mutate the Portfolio](#511-deployment-engine-does-not-mutate-the-portfolio)
    - [5.12 TradePlan Boundary](#512-tradeplan-boundary)
    - [5.13 User Review Is an Architectural Boundary](#513-user-review-is-an-architectural-boundary)
    - [5.14 Current TradeEngine Relationship](#514-current-tradeengine-relationship)
    - [5.15 Trade Logging](#515-trade-logging)
    - [5.16 Separation of Responsibilities](#516-separation-of-responsibilities)
    - [5.17 Relationship to the Drift Engine](#517-relationship-to-the-drift-engine)
    - [5.18 Relationship to the Market Regime Engine](#518-relationship-to-the-market-regime-engine)
    - [5.19 Future Score Integration](#519-future-score-integration)
- [6. Target-Weight Drift Engine](#6-target-weight-drift-engine)
- [7. Analytics Engine](#7-analytics-engine)
- [8. CycleGuard Rules Engine](#8-cycleguard-rules-engine)
- [9. CycleGuard Score Engine](#9-cycleguard-score-engine)
- [10. Streamlit Dashboard](#10-streamlit-dashboard)


---

## 1. Ingestion Pipeline

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

## 1.1 Fidelity provides the source data

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

## 1.2 The CLI starts the ingestion

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

## 1.3 The loader reads the CSV

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

## 1.4 The validator validates the data

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

## 1.5 CycleGuard resolves the account

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

## 1.6 The import is recorded

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

## 1.7 The data is persisted

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
## 1.8 TransactionManager controls the database transaction

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
## 1.9 Import history is completed

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

## 1.10 The import is audited

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

## 1.11 Commit or rollback

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

## 1.12 Success is reported

The final step is to report success to the user.

Conceptually:

```python
CLI → Success message

```
---
## 1.13 What happens when something goes wrong?

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

## 1.14 The ingestion pipeline is designed for traceability and correctness.

* **Import history** traces each import to a specific CSV file.

* **Data validation** ensures that the data is correct before it enters the database.

* **Transaction management** ensures that the database is always in a valid state.

* **Audit checks** verify that the imported data is correct.

---

This design makes CycleGuard imports auditable, reliable, and safe to run.

## 1.15 The complete pipeline
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

> [!NOTE] 
> The ingestion pipeline is responsible for safely transforming Fidelity CSV data into trusted CycleGuard data. The TransactionManager guarantees database atomicity, while Import History provides traceability and the rollback service provides deliberate manual cleanup of committed imports.

This makes ingestion the foundation of CycleGuard: everything that comes later—portfolio aggregation, bucket mapping, market analysis, regime classification, risk scoring, and rebalancing—depends on this pipeline producing accurate and auditable portfolio data.


---

## 1.16 Positions

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

## 1.17 Transactions

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
## 1.18 Snapshots

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

## 1.19 CLI
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


## 2. Bucket Mapper

The Bucket Mapper is the bridge between “what securities does the portfolio contain?” and “what role does each security play in the portfolio?”

The bucket mapper is a feature of the CycleGuard Rebalancing Dashboard. It allows you to map each security in your portfolio to a specific bucket, which is a category of investments.

A bucket regime gives CycleGuard a way to change the desired allocation of the account based on the market environment.

Without regimes, your bucket weights are static:



```bash
Defensive       15%
Fixed Income    30%
TIPS            10%
Core Equity     20%
Equity Income   10%
Growth           7%
High Beta        3%
Foreign          3%
Alternatives     2%
```

A regime says:

>"Given the current market environment, should CycleGuard temporarily use a different set of bucket targets?"

---

## 3 Portfolio Aggregation Engine


The Portfolio Aggregation Engine is the system that answers:

>“How should I allocate my money across all my accounts in the most optimal way?”

It sits at the top level of the CycleGuard architecture, coordinating multiple accounts.

>The Bucket Mapper tells CycleGuard what each position is. The Portfolio Aggregation Engine tells CycleGuard what the portfolio looks like as a whole.

## 3.1. What is the Portfolio Aggregation Engine?

The Portfolio Aggregation Engine (PAE) takes the individual positions in an account and rolls them up into meaningful portfolio-level information.

For example, suppose your Roth IRA contains:

| Position  | Value     | Bucket        |
|-----------|-----------|---------------|
| FZROX     | $25,000   | Core Equity   |
| FTEC      | $14,000   | Equity Growth |
| SOXX      | $12,000   | High Beta     |
| MU        | $7,000    | High Beta     |
| FDRXX     | $20,000   | Defensive     |


The raw ingestion system knows:

    FZROX = $25,000
    FTEC = $14,000
    SOXX = $12,000
    MU = $7,000
FDRXX = $20,000

Bucket Mapper adds:

    FZROX → Core Equity
    FTEC → Equity Growth
    SOXX → High Beta
    MU → High Beta
    FDRXX → Defensive

The Portfolio Aggregation Engine then produces:

    Core Equity = $25,000
    Equity Growth = $14,000
    High Beta = $19,000
    Defensive = $20,000
    Total Portfolio = $78,000

---
https://chatgpt.com/c/6a8e5672-1c74-83e8-b61d-24f392781e0e

The Portfolio Aggregation Engine itself is best understood as a small pipeline that converts raw position data into a structured view of the portfolio.

## 3.2. The architecture

At a high level:

```
                    AccountConfig
                         │
                         │
                         ▼
PositionRepository → PortfolioAggregationService
                         │
                         ├── Position → Bucket mapping
                         │
                         ├── Portfolio value
                         │
                         ├── Bucket values
                         │
                         ├── Bucket weights
                         │
                         ├── Target weights
                         │
                         ├── Bucket drift
                         │
                         └── Position weights
                         │
                         ▼
                 Allocation Models
                         │
             ┌───────────┼───────────┐
             ▼           ▼           ▼
       PositionAllocation
                   BucketAllocation
                              PortfolioAllocation
```

The key point is that PortfolioAggregationService is the coordinator. It doesn't own the database and it doesn't own the configuration. It brings those things together and performs the calculations.

---

## 3.3. The three main inputs

The service gets information from two places.

### 3.3.1. PositionRepository

PositionRepository provides the actual holdings.

For example:

    FZROX    $100,000
    SCHD      $50,000
    FTEC      $20,000

The service asks:

    get_positions(snapshot_id)

which ultimately calls:


    position_repository.get_by_snapshot_with_security(
        snapshot_id
    )

The repository's job is simply:

    "Give me the positions for this snapshot."

It does not calculate allocations.

### 3.3.2. AccountConfig

The service also receives:

    account: AccountConfig

This contains the portfolio's configuration.

For example:

    account.bucket_mapping

might say:

    FZROX → core_equity
    SCHD  → equity_income
    FTEC  → equity_growth

And:

account.bucket_weights

might say:

    core_equity   → 60%
    equity_income → 30%
    equity_growth → 10%

So there is a very important distinction:

PositionRepository
    = What do I actually own?

AccountConfig
    = How is the portfolio supposed to be structured?

---

### 3.3.3. The service sits between them

The central class is:

    PortfolioAggregationService

Its constructor receives both:


    def __init__(
        self,
        position_repository: PositionRepository,
        account: AccountConfig,
    ):


So conceptually:

```
                    ┌─────────────────┐
                    │ Position        │
                    │ Repository      │
                    └────────┬────────┘
                             │
                             │ actual positions
                             ▼
                    ┌──────────────────────┐
                    │                      │
                    │ PortfolioAggregation │
                    │ Service              │
                    │                      │
                    └──────────┬───────────┘
                               ▲
                               │
                    configuration
                               │
                    ┌──────────┴────────┐
                    │   AccountConfig   │
                    └───────────────────┘
```

This is the heart of the architecture.


---
## 3.4. First layer: retrieve positions

The service has:

    get_positions(snapshot_id)

This is deliberately a thin method.

It doesn't calculate anything.

It delegates:

    
    return self.position_repository.get_by_snapshot_with_security(
        snapsho t_id
    )
    

That gives the aggregation layer a collection of position objects.

For example:

    Position
    symbol = FZROX
    current_value = $100,000

    Position
    symbol = SCHD
    current_value = $50,000

---

## 3.5. Second layer: map positions into buckets

Next comes:

    map_positions_to_buckets(snapshot_id)

This uses:

    self.get_bucket_mapping()

which ultimately returns:

    self.account.bucket_mapping

So:

```
Actual Position              Configuration
───────────────              ─────────────
FZROX ─────────────────────→ core_equity
SCHD  ─────────────────────→ equity_income
```

The service then creates:

```
core_equity
    └── FZROX

equity_income
    └── SCHD
```

This is the first major transformation.

We go from:

    list[Position]

to:

    dict[str, list[Position]]

---

## 3.6. Third layer: calculate values

Once positions are grouped, the service can calculate bucket values.

calculate_bucket_values(snapshot_id)

For example:

    FZROX    $100,000
    VTI       $50,000
    SCHD      $50,000

becomes:

    core_equity     $150,000
    equity_income    $50,000

At the same time:

    calculate_portfolio_value(snapshot_id)

produces:

    $200,000

So we now know:

    Portfolio = $200,000

    core_equity     = $150,000
    equity_income    = $50,000


---
## 3.7. Fourth layer: calculate actual weights

Now the service converts dollars into percentages.

    calculate_bucket_weights(snapshot_id)

The formula is:

    bucket market value
    ──────────────────────
    portfolio market value

So:

core_equity:

    $150,000
    ───────── = 75%
    $200,000

and:

equity_income:



We now have the actual portfolio structure.

---

## 3.8. Fifth layer: obtain target weights

The service doesn't calculate target weights.

It retrieves them:

    get_target_weights()

which returns:

    self.account.bucket_weights

For example:

    core_equity     60%
    equity_income   40%

Now we can compare:


                    Actual       Target
                    ──────       ──────
    core_equity       75%          60%
    equity_income     25%          40%


---

## 3.9. Sixth layer: calculate drift

This is where the aggregation engine starts producing information that later components can use.

The service calculates:

    drift = actual_weight - target_weight

Therefore:

    core_equity:

    75% - 60% = +15%

    equity_income:

    25% - 40% = -15%

It also calculates:

    drift_value =
        drift × portfolio_value

So:

    core_equity:

        15% × $200,000 = +$30,000

    equity_income:

        -15% × $200,000 = -$30,000

This is valuable because a later component doesn't have to redo the math.

---

## 3.10. The BucketAllocation model

Rather than returning an unstructured dictionary, the service packages this information into:

BucketAllocation

A bucket therefore looks conceptually like:

    BucketAllocation
    │
    ├── name
    ├── market_value
    ├── actual_weight
    ├── target_weight
    ├── drift
    └── drift_value


For example:

    BucketAllocation
        name          = "core_equity"
        market_value  = $150,000
        actual_weight = 75%
        target_weight = 60%
        drift         = +15%
        drift_value   = +$30,000

This is an important architectural boundary.

The rest of CycleGuard doesn't need to know how the calculation was performed.

It just receives a BucketAllocation.

---

## 3.11. Position allocation is another level

The engine also goes one level deeper.

It can calculate:

    calculate_position_bucket_weights(snapshot_id)

This answers:

    "Within this bucket, how is the money distributed among the positions?"

Suppose:

    core_equity = $150,000

    FZROX = $100,000
    VTI   = $50,000

The service produces:

    FZROX → 66.67%
    VTI   → 33.33%

Those results are represented by:

    PositionAllocation

which contains:

    symbol
    bucket
    market_value
    weight


So there are really two different types of allocation:


    Portfolio
        │
        ├── Bucket allocation
        │       │
        │       ├── actual weight
        │       ├── target weight
        │       └── drift
        │
        └── Position allocation
                │
                └── weight within bucket


---


## 3.12. The top-level PortfolioAllocation

Finally, the service packages the entire result into:

    PortfolioAllocation

Conceptually:


    PortfolioAllocation
    │
    ├── portfolio_value = $200,000
    │
    └── buckets
        │
        ├── core_equity
        │      │
        │      └── BucketAllocation
        │
        └── equity_income
                │
                └── BucketAllocation



This gives the rest of CycleGuard one clean object representing the portfolio's current allocation state.


---

## 3.13. Why this architecture is useful

The most important benefit is separation of responsibilities.

    Repository
        "I retrieve data."

    AccountConfig
        "I define the intended portfolio structure."

    PortfolioAggregationService
        "I calculate what the portfolio actually looks like."

    Allocation models
        "I represent those calculated results."

That means we don't end up with database code mixed with portfolio calculations or trading decisions.


---


## 3.14. What the engine does NOT do

This is just as important.

The aggregation engine does not say:

    BUY FZROX
    SELL SCHD
    MOVE $20,000 TO SGOV

It only tells us:

    core_equity
        actual = 75%
        target = 60%
        drift = +15%
        drift_value = +$30,000

Something else will decide what to do about that drift.


---


## 3.15. The complete Portfolio Aggregation flow

Putting everything together:

```

                  DATABASE
                     │
                     ▼
             PositionRepository
                     │
                     │ positions
                     ▼
        ┌──────────────────────────┐
        │ PortfolioAggregation     │
        │ Service                  │
        │                          │
        │ 1. get_positions()       │
        │           │              │
        │           ▼              │
        │ 2. map_positions...()    │
        │           │              │
        │           ▼              │
        │ 3. bucket values         │
        │           │              │
        │           ▼              │
        │ 4. bucket weights        │
        │           │              │
        │           ▼              │
        │ 5. target weights        │
        │           │              │
        │           ▼              │
        │ 6. drift                 │
        │           │              │
        │           ▼              │
        │ 7. position allocations  │
        └────────────┬─────────────┘
                     │
                     ▼
             PortfolioAllocation
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
   BucketAllocation       PositionAllocation

```

And AccountConfig feeds the service from the side:

```
                         AccountConfig
                              │
                 ┌────────────┴────────────┐
                 │                         │
          bucket_mapping             bucket_weights
                 │                         │
                 └────────────┬────────────┘
                              ▼
                 PortfolioAggregationService
```

> The Portfolio Aggregation Engine takes actual positions plus portfolio configuration and transforms them into a structured, calculated representation of the portfolio's current allocation and drift.

---

## 4 Market Regime Engine

> A modular, configurable framework that evaluates multiple independent market signals—including trend, breadth, volatility, leadership, credit, valuation (CAPE), momentum, and potentially rates—to determine the current market regime and regime score. Individual indicators are implemented as independent signal modules so additional indicators can be added without modifying the core regime engine.

```
                    PHASE 4
             MARKET REGIME ENGINE
                       │
          ┌────────────┴────────────┐
          │                         │
     Market Data                Configuration
          │                         │
          └────────────┬────────────┘
                       ▼
              Signal Registry
                       │
      ┌────────────────┼────────────────┐
      │                │                │
      ▼                ▼                ▼
   Trend            Breadth          Volatility
   Signal            Signal            Signal
      │                │                │
      ├───────┬────────┼────────┬───────┤
      ▼       ▼        ▼        ▼       ▼
 Leadership Credit   CAPE    Momentum  Rates
      │       │        │        │       │
      └───────┴────────┴────────┴───────┘
                       │
                       ▼
                Signal Aggregator
                       │
                       ▼
                 Regime Scorer
                       │
                       ▼
               Regime Classifier
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
       RISK_ON     TRANSITION    DEFENSIVE
```
----
## 4.1 Market Regime Engine Architecture


#### 4.1.1 Purpose

The Market Regime Engine determines the current overall market environment by evaluating a collection of independent market signals and then combining those signal results into a single market regime.

Its job is not to decide what to buy or sell.

Instead, it answers:

"What kind of market are we currently in?"

For example:

    RISK_ON
    TRANSITION
    RISK_OFF

That regime becomes an important input to later CycleGuard components such as the Deployment Engine and Rules Engine.

----

#### 4.1.2 Where It Fits in CycleGuard

The Market Regime Engine sits between market data and portfolio decision-making.

```
                     MARKET DATA
                         │
                         ▼
              ┌─────────────────────┐
              │   Market Data Layer  │
              │                     │
              │ Prices              │
              │ Moving averages     │
              │ VIX                 │
              │ CAPE                │
              │ Credit data         │
              └──────────┬──────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │  MARKET REGIME      │
              │      ENGINE         │
              │                     │
              │  SignalFactory      │
              │       ↓             │
              │  SignalAggregator   │
              │       ↓             │
              │  RegimeClassifier   │
              └──────────┬──────────┘
                         │
                         ▼
                Market Regime
             ┌──────────────────┐
             │ RISK_ON          │
             │ TRANSITION       │
             │ RISK_OFF         │
             └────────┬─────────┘
                      │
                      ▼
             ┌────────────────────┐
             │ Deployment Engine  │
             └────────┬───────────┘
                      │
                      ▼
                Portfolio Actions
```
The important separation is:

Market Regime Engine determines the environment.

Deployment Engine determines what to do about that environment.

----

#### 4.1.3 High-Level Architecture

The engine consists of four primary components:

    RegimeEngine
        │
        ├── SignalFactory
        │
        ├── SignalAggregator
        │
        └── RegimeClassifier

The individual signals sit underneath the aggregator:

    SignalAggregator
        │
        ├── TrendSignal
        ├── BreadthSignal
        ├── VolatilitySignal
        ├── LeadershipSignal
        ├── CreditSignal
        └── CapeSignal

##### 4.1.3.1 What is a signal?

In CycleGuard, a signal is a small, specialized piece of logic that looks at a specific aspect of the market and converts raw market data into a standardized market condition.

Think of a signal as answering one question.

Example

| Signal         | Question it answers                                        | Example output |
| -------------- | ---------------------------------------------------------- | -------------- |
| **Trend**      | Is the broad market above/below its major moving averages? | `bullish`      |
| **Breadth**    | How broadly is the market participating?                   | `Strong`       |
| **Volatility** | Is market volatility elevated?                             | `Calm`         |
| **Leadership** | Are important growth/risk assets leading?                  | `Strong`       |
| **Credit**     | Are credit markets healthy or stressed?                    | `Healthy`      |
| **CAPE**       | Is valuation supportive or restrictive?                    | `Elevated`     |

So the architecture is:

```
                    Raw Market Data
                          │
          ┌───────────────┼────────────────┐
          ▼               ▼                ▼
       Trend           Breadth          Volatility
          │               │                │
          ▼               ▼                ▼
      bullish           Strong            Calm
          
          ┌───────────────┼────────────────┐
          ▼               ▼                ▼
      Leadership        Credit             CAPE
          │               │                │
          ▼               ▼                ▼
        Strong          Healthy          Elevated
                          │
                          ▼
                Signal Aggregator
                          │
                          ▼
                 Regime Classifier
                          │
                          ▼
                     RISK_ON

```

A signal is NOT a regime

This distinction is important.

A signal is an individual observation:

    Trend = bullish
    Breadth = Strong
    Credit = Healthy


A **regime** is the conclusion drawn from the collection of signals:

    ***RISK_ON***

So:

> Signals provide the evidence. The Regime Engine interprets the evidence.

##### 4.1.3.2 Why make signals separate?

Because each signal has one responsibility.

For example, your TrendSignal currently evaluates price relative to moving averages.

    Conceptually:

        TrendSignal.evaluate(data)
            ↓
        SPY price
        SPY 50-DMA
        SPY 200-DMA
            ↓
        "bullish"

Your BreadthSignal does something completely different:

    BreadthSignal.evaluate(data)
            ↓
    sector prices
    sector 50-DMAs
            ↓
    percentage above 50-DMA
            ↓
    "Strong"


And CreditSignal evaluates yet another thing:

    CreditSignal.evaluate(data)
            ↓
    JNK / SHY relationship
            ↓
    "Healthy"

Each can therefore be developed and tested independently.


In software terms

A signal is essentially a market-condition detector.

Your architecture has a common interface:

    class MarketSignal:
        def evaluate(self, data):
            ...

Then you have implementations:

    MarketSignal
        │
        ├── TrendSignal
        ├── BreadthSignal
        ├── VolatilitySignal
        ├── LeadershipSignal
        ├── CreditSignal
        └── CapeSignal

The SignalFactory creates the appropriate signal from your YAML configuration:

    regime.yaml
        │
        ▼
    SignalFactory
        │
        ├── trend → TrendSignal
        ├── breadth → BreadthSignal
        ├── volatility → VolatilitySignal
        ├── leadership → LeadershipSignal
        ├── credit → CreditSignal
        └── cape → CapeSignal

The SignalAggregator then evaluates all of them:

    signal_results = aggregator.evaluate(data)

Producing something conceptually like:

    {
        "trend": {
        "status": "bullish"
        },
        "breadth": {
            "status": "Strong"
        },
        "volatility": {
            "status": "Calm"
        },
        "leadership": {
            "status": "Strong"
        },
        "credit": {
            "status": "Healthy"
        },
        "cape": {
            "status": "Elevated"
        }
    }

The RegimeClassifier consumes that collection of signals and determines the regime.

The key CycleGuard concept
    MARKET DATA
        ↓
    SIGNALS
        ↓
    MARKET REGIME
        ↓
    DEPLOYMENT DECISION
        ↓
    PORTFOLIO ACTION

So when we say "the next engine consumes the regime output," we're talking about moving one level up the hierarchy:

    ***Signals → Regime → Deployment***

The signal is the lowest-level market interpretation in this part of CycleGuard.







----

#### 4.1.4 RegimeEngine

The RegimeEngine is the orchestrator.

Its responsibility is intentionally simple:

1. Read signal configuration.
2. Create the configured signals.
3. Pass market data to the signals.
4. Collect their results.
5. Pass those results to the classifier.
6. Return the signals and resulting regime.

Conceptually:


```
signal_results = aggregator.evaluate(data)

regime = classifier.classify(signal_results)

return {
    "signals": signal_results,
    "regime": regime,
}
```

The engine therefore does not contain the logic for determining whether the market is bullish, bearish, healthy, etc.

That logic belongs to the individual signals.

----
#### 4.1.5 SignalFactory

The SignalFactory is a simple factory pattern implementation. Its job is to create the signals requested in the configuration.

For example, if the config says:

```yaml
signals:
  - type: trend
  - type: breadth
```

`SignalFactory` will:

Create a TrendSignal instance
Create a BreadthSignal instance
Return a list of those two signals
It is intentionally simple and stateless. It does not evaluate signals or hold market data.

----
#### 4.1.6 SignalAggregator

The SignalAggregator is the component that collects results from individual signals and combines them.

Conceptually:

```
Input = list of evaluated signals

Output = dictionary of all signal results
```

Importantly, the aggregator does **not** decide whether the market is bullish, bearish, healthy, etc.

That is the job of the RegimeClassifier.

The aggregator simply:

Receives results from TrendSignal, BreadthSignal, VolatilitySignal, etc.
Organizes them into a single dictionary.
Passes that dictionary to the classifier.

Example structure:

```python
{
    "trend": {
        "name": "trend",
        "status": "bullish",
        "value": 0.7,
    },
    "breadth": {
        "name": "breadth",
        "status": "strong",
        "value": 0.85,
    },
    "volatility": {
        "name": "volatility",
        "status": "calm",
        "value": 0.2,
    },
    # ... all other signals
}
```

The aggregator is intentionally simple. It does not perform complex logic—just collection and formatting.

----
#### 4.1.7 The Six Market Signals

The current architecture contains six configured signals. In CycleGuard, a signal is a small, specialized piece of logic that looks at a specific aspect of the market and converts raw market data into a standardized market condition.

Think of a signal as answering one question.

Example

    Your Market Regime Engine currently has six signals:

    | Signal | Question it answers | Example output |
    |--------|--------------------|----------------|
    | Trend  | Is the broad market above/below its major moving averages? | bullish |
    | Breadth | How broadly is the market participating? | Strong |
    | Volatility | Is market volatility elevated? | Calm |
    | Leadership | Are important growth/risk assets leading? | Strong |
    | Credit | Are credit markets healthy or stressed? | Healthy |
    | CAPE   | Is valuation supportive or restrictive? | Elevated |

So the architecture is:
```
                    Raw Market Data
                          │
          ┌───────────────┼────────────────┐
          ▼               ▼                ▼
       Trend           Breadth          Volatility
          │               │                │
          ▼               ▼                ▼
      bullish           Strong            Calm
          
          ┌───────────────┼────────────────┐
          ▼               ▼                ▼
      Leadership        Credit             CAPE
          │               │                │
          ▼               ▼                ▼
        Strong          Healthy          Elevated
                          │
                          ▼
                Signal Aggregator
                          │
                          ▼
                 Regime Classifier
                          │
                          ▼
                     RISK_ON
```

The Market Regime Engine establishes the interface that every regime signal must implement. It defines a class:

```
class MarketSignal(ABC):
    """
    Base contract for all CycleGuard market regime signals.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the unique name of the signal."""
        raise NotImplementedError

    @abstractmethod
    def evaluate(self, data: Any) -> dict:
        """
        Evaluate the signal using supplied market data.

        Returns:
            A dictionary containing the signal result.
        """
        raise NotImplementedError
```
It establishes the interface that every regime signal must implement. Each signal must have:

    A `name` property.

    An `evaluate()` method that accepts market data and returns a result.

This ensures that:

    All signals expose the same interface.

    The SignalAggregator can collect results consistently.

    The RegimeClassifier receives standardized input.

This makes CycleGuard modular and easy to extend: to add a new signal, you simply create a new class that implements the MarketSignal interface.

For example:

A trend implementation could therefore look like:

```
class TrendSignal(MarketSignal):

    @property
    def name(self) -> str:
        return "trend"

    def evaluate(self, data: Any) -> dict:
        return {
            "signal": "bullish",
            "score": 80,
            "confidence": 0.85,
        }
```
The important architectural point is that the regime engine doesn't need to know how TrendSignal works.

It only needs to know:

    MarketSignal
        │
        ├── name
        └── evaluate(data)

This abstraction is valuable because new signals can be added without changing the core regime engine.

For example, later you could add:

    class CreditSpreadSignal(MarketSignal):
        ...

and register it with the engine without modifying the existing trend, breadth, or volatility implementations

The clean separation is:

    MarketSignal
        ↓
    Individual market condition

    Signal Aggregator
        ↓
    Combines signals

    Regime Classifier
        ↓
    Determines regime

    Regime Output
        ↓
    Consumed by the next CycleGuard engine

That separation is particularly important for what comes next: the next engine should consume the regime output rather than directly consuming the individual market signals.

So this MarketSignal class is essentially the plug-in interface for the signal layer of the Market Regime Engine.

#### 4.1.7.1 Trend Signal

Measures broad market trend using the configured proxy, currently SPY.

Conceptually:

    ```
    SPY price
    │
    ├── compared with 50 DMA
    │
    └── compared with 200 DMA
    ```

It produces:

    ```
    bullish
    neutral
    bearish
    ```

The signal uses its configured proxy rather than hard-coding the market instrument.

#### 4.1.7.2 Breadth Signal

Breadth asks:

> How many of the selected market sectors are trading above their 50-day moving average?

The current default proxy group contains the 11 major sector ETFs:
    XLC
    XLY
    XLP
    XLE
    XLF
    XLV
    XLI
    XLB
    XLRE
    XLK
    XLU


Measures market breadth by counting how many stocks in the configured universe are above their 50-day moving averages.

The signal evaluates:

    A list of input symbols (usually ETF constituents).
    Each symbol’s latest price.
    Each symbol’s 50-day moving average.

It categorizes the result as:

    * strong if all stocks are above their 50-day moving averages
    * weak if no stocks are above their 50-day moving averages
    * mixed otherwise

This signal is **not** reliant on SPY. It can run independently using any universe of stocks defined in the configuration.

Conceptually:

    Universe of stocks
           │
           ▼
    [Symbol A > 50 DMA?]
    [Symbol B > 50 DMA?]
    [Symbol C > 50 DMA?]
           │
           ▼
    Count = 24 out of 25 → Strong

Output categories:

    strong
    mixed
    weak

The breadth signal is a pure equity-based signal and does not depend on SPY, interest rates, or credit spreads.


#### 4.1.7.3 Volatility Signal

Uses the VIX to determine whether volatility conditions are supportive or defensive.

Conceptually:

    VIX
     │
     ├── low → calm
     ├── intermediate → elevated/transition
     └── high → risk-off

The thresholds are configuration-driven.

This gives the regime engine an explicit measurement of market stress.    

#### 4.1.7.4 Leadership Signal

Leadership measures whether the configured leading assets are participating in the market trend.

The current configuration includes instruments such as:

    QQQ
    SMH

The signal checks their relationship to their 50-day moving averages.

For example:

    QQQ > 50 DMA  → participating
    SMH > 50 DMA  → participating

Possible outcomes:

    Strong
    Mixed
    Weak

This is different from breadth.

Breadth asks:

> How broad is participation?

Leadership asks:

Are the important growth/leadership areas participating?

That distinction is useful for CycleGuard.



#### 4.1.7.5 Credit Signal

Credit provides another risk measurement.

It compares configured credit/risk assets, currently using the relationship between the configured instruments such as:

    JNK
    SHY

The signal compares the current ratio with its 50-day ratio.

Conceptually:

    Current JNK/SHY
           vs.
    50-day JNK/SHY

Result:

    Healthy
    Stressed

This gives the regime engine information that equity price trends alone cannot provide.


#### 4.1.7.6 Cape Signal

CAPE provides a valuation perspective.

Unlike trend, breadth, volatility, and credit, CAPE is not primarily measuring short-term market momentum.

It answers a different question:

> How expensive is the market relative to its historical earnings valuation?

This gives CycleGuard a longer-term valuation context.

Importantly, the CAPE signal is still treated like every other signal by the architecture:

    market data
        ↓
    CapeSignal
        ↓
    status
        ↓
    SignalAggregator

The classifier can then incorporate that status into regime determination if the configuration specifies it.

-----
#### 4.1.8 Regime Classifier

The RegimeClassifier is the final piece of the Market Regime Engine. Its job is to:

Take the dictionary of signal results from SignalAggregator

Apply logic to determine the current market regime

Return the regime name

Conceptually:

```
Input = Signal results dictionary

Output = Regime name
```

The classifier contains the rules that translate the six signals into one of the four market regimes.

-----

#### 4.1.9 Configuration-Driven Classification


The classifier does not hard-code regime rules.

Instead, the rules live in:

    src/config/system/regime.yaml


This is a major architectural decision.

Conceptually:

    regimes:

    RISK_ON:
        conditions:
        trend: bullish
        breadth: Strong
        volatility: calm
        leadership: Strong
        credit: Healthy

    TRANSITION:
        conditions:
        ...

    RISK_OFF:
        conditions:
        ...

The exact conditions are controlled by the YAML configuration.

Therefore the **engine code doesn't need to change simply because the investment rules change.**


#### 4.1.10 All Conditions Must Match

The classifier uses an AND relationship.

For a regime to match:

    Trend       ──┐
    Breadth     ──┤
    Volatility  ──┤
    Leadership  ──┼── ALL must match
    Credit      ──┤
    CAPE        ──┘
                    │
                    ▼
                REGIME

For example:

    RISK_ON

    trend       = bullish       ✓
    breadth     = Strong        ✓
    volatility  = calm          ✓
    leadership  = Strong        ✓
    credit      = Healthy       ✓

Therefore:

    RISK_ON

If even one required condition does not match, that regime is not selected.


#### 4.1.11 Configuration Order Matters

Regimes are evaluated in YAML/configuration order.

The classifier effectively does:

    for regime in configured_regimes:

        if all_conditions_match:
            return regime

The first matching regime wins.

This means the configuration should be ordered deliberately when regimes could potentially overlap.

#### 4.1.12 TRANSITION Is the Safety Net


If none of the configured regimes match:

    RISK_ON       ✗
    RISK_OFF      ✗
    other regimes ✗
        │
        ▼
    TRANSITION

The fallback is:

    TRANSITION

This is important.

The system does not have to force an ambiguous market into either bullish or bearish.

That is particularly useful for a portfolio-management system.


#### 4.1.13 Data Flow

The complete execution flow looks like this:


    Market Data
        │
        ▼
    RegimeEngine.evaluate()
        │
        ▼
    SignalAggregator
        │
        ├──────────────┐
        ▼              ▼
    Trend          Breadth
        │              │
        ├──────┐       │
        ▼      ▼       ▼
    Volatility Leadership Credit
        │      │       │
        └──────┴───────┴──────┐
                                ▼
                            CAPE
                                │
                                ▼
                    Signal Results Dictionary
                                │
                                ▼
                        RegimeClassifier
                                │
                                ▼
                        Configured Rules
                                │
                                ▼
                        Market Regime



##### 4.1.13.1 Example


Suppose the engine receives:

    SPY       = 105
    SPY 50DMA = 100
    SPY 200DMA = 100

    VIX       = 15

    QQQ       = 105
    QQQ 50DMA = 100

    SMH       = 105
    SMH 50DMA = 100

    JNK       = 105
    SHY       = 100
    ...

The individual signals might produce:

    Trend       → bullish
    Breadth     → Strong
    Volatility  → calm
    Leadership  → Strong
    Credit      → Healthy
    CAPE        → ...

The classifier then evaluates the configured conditions.

If the RISK_ON conditions are satisfied:

             ┌───────────────┐
             │    RISK_ON    │
             └───────────────┘

If the market is mixed:

             ┌───────────────┐
             │   TRANSITION  │
             └───────────────┘



#### 4.1.14 Why This Architecture Is Valuable

The architecture gives CycleGuard separation of concerns.

| Component        | Responsibility                      |
| ---------------- | ----------------------------------- |
| Market data      | Provides observations               |
| Signal           | Interprets one aspect of the market |
| SignalFactory    | Creates signals                     |
| SignalAggregator | Executes signals                    |
| RegimeClassifier | Determines regime                   |
| RegimeEngine     | Orchestrates the process            |
| `regime.yaml`    | Defines investment/regime rules     |


That means we can change one layer without unnecessarily changing the others.

For example, changing:

    VIX threshold

doesn't require rewriting RegimeEngine.

Adding:

    Treasury yield-curve signal

doesn't require rewriting RegimeClassifier.

Changing:

    RISK_ON conditions

doesn't require changing signal implementation.


#### 4.1.15 Relationship to the Portfolio Engine

The most important distinction going forward is:

                 MARKET REGIME ENGINE
                         │
                         │
                  "What is happening?"
                         │
                         ▼
                     RISK_ON
                    TRANSITION
                     RISK_OFF
                         │
                         ▼
                 DEPLOYMENT ENGINE
                         │
                         │
                  "What should we do?"
                         │
                         ▼
                 Capital deployment
                         │
                         ▼
                 Portfolio allocation


The Market Regime Engine does not rebalance the portfolio.

It provides the environmental context that later engines can use.



#### 4.1.16 Architectural Principle

> **Signals measure. The classifier decides. The engine orchestrates. Configuration defines the rules.**

-----

The next engine should consume its output and translate the market regime into portfolio-level decisions.

For CycleGuard, I would make the next engine the Deployment Engine.

----

## 5. Deployment Engine

> The Regime Engine determines the market environment. The Deployment Engine determines what CycleGuard should do with available capital.


    Market Data
        │
        ▼
    Market Regime Engine
        │
        │  regime = RISK_ON
        │  confidence = 82
        │  score = 78
        ▼
    Deployment Engine
        │
        │  "Given this regime, should we deploy cash?"
        │
        ▼
    Deployment Decision
        │
        ├── deploy / hold / reduce
        ├── deployment percentage
        ├── eligible buckets
        ├── eligible securities
        └── dollar amounts
        │
        ▼
    Target-Weight / Trade Engine
        │
        ▼
    Trade List


#### 5.1 Purpose

| Engine               | Role                        |
| -------------------- | --------------------------- |
| Market Regime Engine | Evaluates market              |
| **Deployment Engine**| Decides whether to deploy     |
| Trade Engine         | Decides what to trade         |
| Target-Weight Engine | Adjusts portfolio structure |

The Deployment Engine is the CycleGuard component responsible for deciding when and how much capital should be deployed into the portfolio.

Its primary responsibility is to transform a market or portfolio condition into a Deployment Decision.

The Deployment Engine answers questions such as:

* Should CycleGuard deploy capital?
How much capital should be deployed?
* Why is the capital being deployed?
Which deployment mechanism should be used?
* Regime-based deployment
* Crash deployment
* Other future deployment strategies
* What level of deployment has been triggered?

The Deployment Engine does not determine the final BUY/SELL transactions.

That responsibility belongs downstream to the Trade Planning / Trade Engine.

#### 5.2 Where the Deployment Engine Fits

The Deployment Engine sits between CycleGuard's market/risk analysis and its trade-generation infrastructure.

The high-level architecture is:

```text
Market / Portfolio State
          ↓
      Regime / Rules / Scores
          ↓
   Deployment Decision
          ↓
   Allocation / Drift
          ↓
       TradePlan
          ↓
     User Approval
          ↓
      Actual Trade
          ↓
    Transaction Ingestion
          ↓
     Updated Portfolio
```

The important architectural boundary is:

> Deployment decides how much capital to deploy. Trade planning decides what transactions are required to implement that deployment.


#### 5.3 Deployment vs. Trading

CycleGuard intentionally separates investment decisions from transaction generation.

For example, suppose CycleGuard determines:

Crash Level: Level 1
Deployment Amount: $10,000
Reason: Market drawdown triggered Level 1

The Deployment Engine has completed its job.

It does not need to decide:

SELL $10,000 SGOV
BUY $4,000 FZROX
BUY $3,000 SCHD
BUY $2,000 FZILX
BUY $1,000 IEMG

Those are trade-planning decisions.

The architecture therefore separates:

```text
DEPLOYMENT DECISION
        │
        │ "Deploy $10,000"
        ▼
TRADE PLANNING
        │
        │ "Here are the transactions required"
        ▼
TRADE PLAN
```

This separation is important because it prevents the Deployment Engine from becoming responsible for portfolio construction, security selection, and brokerage execution.



#### 5.4 Core Responsibility

The core responsibility of the Deployment Engine is to transform market/portfolio conditions into deployment decisions.

```text
Market / Portfolio Condition
            │
            ▼
      Deployment Logic
            │
            ▼
    Deployment Decision
```

A deployment decision should contain information such as:`

- deployment amount
- deployment level
- deployment reason
- deployment strategy

Conceptually:

```text
DeploymentDecision(
    amount=Decimal("10000.00"),
    level="Level 1",
    reason="Market drawdown exceeded Level 1 threshold",
    strategy="crash",
)
```

The exact implementation can evolve, but the architectural principle remains the same.

#### 5.5 How the Deployment Engine Works

The Deployment Engine operates by transforming market/portfolio conditions into deployment decisions.

1. **Input**: Accepts market/portfolio conditions
2. **Logic**: Applies deployment rules/strategies
3. **Output**: Generates deployment decision

This process can be summarized as:

```text
Input Conditions     →   Deployment Logic     →   Deployment Decision
(market/portfolio)       (rules, strategies)      (amount, level, reason)
```

The Deployment Engine can support multiple deployment strategies, such as:

- **Regime-based deployment** - deploy based on current market regime
- **Crash deployment** - deploy during market crashes
- **Drift-based deployment** - deploy when portfolio deviates from targets

Each strategy has its own logic for determining:

- Whether to deploy
- How much to deploy
- Which buckets/assets are eligible
- The reason for deployment

The Deployment Engine serves as the central hub for all deployment-related decisions, ensuring that:

- Deployment decisions are consistent with market conditions
- Deployment strategies can be easily added or modified
- Deployment decisions are clearly documented
- Deployment decisions are separated from trade-level details

This architectural separation makes the system more maintainable, testable, and easier to understand.

#### 5.6 Deployment Strategies
##### 5.6.1 Regime-Based Deployment

Regime-based deployment is a strategy that adjusts deployment decisions based on the current market regime. 

The Deployment Engine can support multiple deployment strategies, such as:

- Regime-based deployment - deploy based on current market regime
- Crash deployment - deploy during market crashes
- Drift-based deployment - deploy when portfolio deviates from targets

Each strategy has its own logic for determining:

- Whether to deploy
- How much to deploy
- Which buckets/assets are eligible
- The reason for deployment

The Deployment Engine serves as the central hub for all deployment-related decisions, ensuring that:

- Deployment decisions are consistent with market conditions
- Deployment strategies can be easily added or modified
- Deployment decisions are clearly documented
- Deployment decisions are separated from trade-level details

This architectural separation makes the system more maintainable, testable, and easier to understand.

##### 5.6.2 Crash-Based Deployment

Crash-based deployment is a strategy that adjusts deployment decisions based on the current market regime. 

The Deployment Engine can support multiple deployment strategies, such as:

- Regime-based deployment - deploy based on current market regime
- Crash deployment - deploy during market crashes
- Drift-based deployment - deploy when portfolio deviates from targets

Each strategy has its own logic for determining:

- Whether to deploy
- How much to deploy
- Which buckets/assets are eligible
- The reason for deployment

The Deployment Engine serves as the central hub for all deployment-related decisions, ensuring that:

- Deployment decisions are consistent with market conditions
- Deployment strategies can be easily added or modified
- Deployment decisions are clearly documented
- Deployment decisions are separated from trade-level details

This architectural separation makes the system more maintainable, testable, and easier to understand.

#### 5.7 Crash Deployment

Crash deployment is a separate deployment mechanism designed to deploy capital when the market experiences significant declines.

The current TradeEngine implementation supports crash deployment levels.

Conceptually:

```text
Market Drawdown
      │
      ▼
Crash Detection
      │
      ▼
Crash Level
      │
      ├── Level 1
      ├── Level 2
      ├── Level 3
      └── ...
      │
      ▼
Deployment Amount
```

For example:

```text
Level 1
   ↓
Deploy $X

Level 2
   ↓
Deploy $Y

Level 3
   ↓
Deploy $Z
```

The crash deployment mechanism therefore provides a disciplined way of deploying cash during market declines rather than relying on discretionary decisions.


#### 5.8 Drawdown Detection

Drawdown detection is the mechanism that determines whether the market has experienced a significant decline triggering crash deployment.

The current TradeEngine implementation supports crash deployment levels.

Conceptually:

```text
Market Drawdown
      │
      ▼
Crash Detection
      │
      ▼
Crash Level
      │
      ├── Level 1
      ├── Level 2
      ├── Level 3
      └── ...
      │
      ▼
Deployment Amount
```

For example:

```text
Level 1
   ↓
Deploy $X

Level 2
   ↓
Deploy $Y

Level 3
   ↓
Deploy $Z
```

The crash deployment mechanism therefore provides a disciplined way of deploying cash during market declines rather than relying on discretionary decisions.

#### 5.8.1 Drawdown Calculation

Drawdown calculation is the mechanism that determines whether the market has experienced a significant decline triggering crash deployment.

The current TradeEngine implementation supports crash deployment levels.

Conceptually:

```text
Market Drawdown
      │
      ▼
Crash Detection
      │
      ▼
Crash Level
      │
      ├── Level 1
      ├── Level 2
      ├── Level 3
      └── ...
      │
      ▼
Deployment Amount
```

For example:

```text
Level 1
   ↓
Deploy $X

Level 2
   ↓
Deploy $Y

Level 3
   ↓
Deploy $Z
```

The crash deployment mechanism therefore provides a disciplined way of deploying cash during market declines rather than relying on discretionary decisions.


#### 5.8.2 Crash Levels

Crash levels are the thresholds that determine whether the market has experienced a significant decline triggering crash deployment.

The current TradeEngine implementation supports crash deployment levels.

Conceptually:

```text
Market Drawdown
      │
      ▼
Crash Detection
      │
      ▼
Crash Level
      │
      ├── Level 1
      ├── Level 2
      ├── Level 3
      └── ...
      │
      ▼
Deployment Amount
```

For example:

```text
Level 1
   ↓
Deploy $X

Level 2
   ↓
Deploy $Y

Level 3
   ↓
Deploy $Z
```

The crash deployment mechanism therefore provides a disciplined way of deploying cash during market declines rather than relying on discretionary decisions.


#### 5.8.3 Crash Deployment Levels

Crash levels are the thresholds that determine whether the market has experienced a significant decline triggering crash deployment.

The current TradeEngine implementation supports crash deployment levels.

Conceptually:

```text
Market Drawdown
      │
      ▼
Crash Detection
      │
      ▼
Crash Level
      │
      ├── Level 1
      ├── Level 2
      ├── Level 3
      └── ...
      │
      ▼
Deployment Amount
```

For example:

```text
Level 1
   ↓
Deploy $X

Level 2
   ↓
Deploy $Y

Level 3
   ↓
Deploy $Z
```

The crash deployment mechanism therefore provides a disciplined way of deploying cash during market declines rather than relying on discretionary decisions.

#### 5.9 Cash Is a Deployment Resource

CycleGuard does not treat every dollar in the portfolio as deployable.

The current architecture uses the portfolio's defensive bucket as the source of available deployment capital.

Conceptually:

```text
Portfolio
   │
   ├── Core Equity
   ├── Equity Income
   ├── Equity Growth
   ├── Foreign Equity
   ├── Alternatives
   └── Defensive
          │
          ▼
     Deployment Capital
```

This is important because CycleGuard's portfolio architecture already defines the purpose of each bucket.

The Deployment Engine should therefore consume the portfolio's bucket information rather than inventing a separate concept such as an AVAILABLE_CAPITAL bucket.

#### 5.10 Cash Deployment Policy

The Cash Deployment Policy is a planned component of Phase 5.

It will determine how much of the available defensive capital can actually be released when a deployment event occurs.

This is different from detecting the deployment event.

For example:

`
Deployment Trigger
       │
       ▼
Deploy $20,000
       │
       ▼
Cash Deployment Policy
       │
       ├── Required reserve
       ├── Maximum deployment
       ├── Staging rules
       └── Available defensive capital
       │
       ▼
Approved Deployment Amount
```


This distinction allows CycleGuard to separate:

    Why should we deploy?

from:

    How much cash are we willing to release?

#### 5.11 Deployment Engine Does Not Mutate the Portfolio

A critical design decision is that the Deployment Engine is proposal-oriented.

It should not directly modify the portfolio.

For example, this is not the intended behavior:

    portfolio["SGOV"] -= 10000
    portfolio["FZROX"] += 10000

Instead:

```text
Current Portfolio
       │
       ▼
Deployment Engine
       │
       ▼
Deployment Decision
       │
       ▼
Trade Planning
       │
       ▼
TradePlan
```

The actual portfolio changes only after the transactions occur externally and are subsequently captured by CycleGuard's transaction ingestion pipeline.

#### 5.12 TradePlan Boundary

The TradePlan is the boundary between CycleGuard's decision-making and the user's actual brokerage activity.

The current architecture is:

```text
DeploymentDecision
       │
       ▼
TradeEngine
       │
       ▼
TradePlan
       │
       ├── deployment_amount
       ├── sells
       ├── buys
       └── reason

```

A TradePlan contains proposed Trade objects.

A Trade contains:

    symbol
    action
    amount

For example:

    SELL SGOV $10,000
    BUY FZROX $5,000
    BUY SCHD  $3,000
    BUY IEMG  $2,000

The TradePlan is a proposal.

CycleGuard does not send these trades directly to Fidelity.


#### 5.13 User Review Is an Architectural Boundary

CycleGuard is designed as a decision-support and portfolio-management system, not an autonomous brokerage execution system.

The intended workflow is:

```text
CycleGuard
    │
    ▼
Deployment Decision
    │
    ▼
TradePlan
    │
    ▼
USER REVIEW
    │
    ├── Approve
    ├── Modify
    └── Reject
    │
    ▼
FIDELITY
    │
    ▼
Actual Transactions
    │
    ▼
CycleGuard Transaction Ingestion
```

This creates an important safety boundary.

CycleGuard can calculate and recommend trades without having authority to execute them.


#### 5.14 Current TradeEngine Relationship

The current TradeEngine is responsible for turning deployment information into a proposed set of transactions.

It contains functionality for:

    * calculating portfolio value
    * applying position limits
    * generating crash trades
    * generating a TradePlan
    * executing the deployment workflow in the sense of orchestrating proposal generation and logging
    * calculating remaining deployment capital

The important recent architectural change is that the TradeEngine no longer has an apply_trades() method.

That method would have mutated the portfolio.

It was removed because the portfolio should represent observed portfolio state, not a simulated state created by the trade engine.


#### 5.15 Trade Logging

Trade logging has been separated from the TradeEngine.

The architecture is now:

```text
TradeEngine
     │
     ▼
ITradeLogger
     │
     ▼
CSVTradeLogger
```

ITradeLogger defines the logging contract.

CSVTradeLogger provides the current implementation.

The logger records proposed trades and their reason.

This keeps logging concerns separate from deployment and trade-generation logic.


#### 5.16 Separation of Responsibilities

CycleGuard deliberately assigns different responsibilities to different engines.

|Component|Responsibility|
|--------|----------------|
|Ingestion Engine|Obtain portfolio/transaction data|
|Portfolio Aggregation Engine|Construct the current portfolio view|
|Bucket Mapper|Map securities to portfolio buckets|
|Market Regime Engine|Determine the current market regime|
|Deployment Engine|Decide whether/how much capital should be deployed|
|Cash Deployment Policy|Determine how much available cash can be released|
|Target-Weight / Drift Engine|Determine where portfolio capital should be allocated|
|Trade Engine|Convert allocation requirements into proposed trades|
|TradePlan|Represent the proposed transactions|
|Transaction Ingestion|Capture what actually happened|
|Analytics Engine|Analyze portfolio behavior and results|
|Rules Engine|Apply deterministic portfolio rules|
|Score Engine|Calculate portfolio/market scores|
|Deployment Priority Score|Rank/quantify deployment urgency|
|AI Analyst|Explain, analyze, challenge, and recommend|

This separation is one of the most important architectural characteristics of CycleGuard.



#### 5.17 Relationship to the Drift Engine

The Deployment Engine and Target-Weight / Drift Engine have different jobs.

**Deployment Engine**

    Answers:

    > How much money should we deploy?

**Drift Engine**

    Answers:

    > Where does that money need to go?

For example:

```text
Deployment Engine
       │
       ▼
Deploy $20,000
       │
       ▼
Drift Engine
       │
       ├── FZROX is underweight → $8,000
       ├── SCHD is underweight  → $5,000
       ├── FZILX is underweight → $4,000
       └── IEMG is underweight  → $3,000
       │
       ▼
Trade Engine
       │
       ▼
TradePlan
```

This prevents deployment logic from becoming entangled with portfolio allocation logic.

#### 5.18 Relationship to the Market Regime Engine

The Market Regime Engine and Deployment Engine are also separate.

The Market Regime Engine answers:

> **What kind of market environment are we currently in?**

The Deployment Engine answers:

> **What should CycleGuard do with capital given that environment?**

Therefore:

```text
Market Data
    │
    ▼
Market Regime Engine
    │
    ▼
RISK_ON / NEUTRAL / RISK_OFF / CRISIS
    │
    ▼
Deployment Engine
    │
    ▼
Deployment Decision
```

The Deployment Engine should consume regime information rather than duplicate regime classification logic.

#### 5.19 Future Score Integration

The future CycleGuard Score Engine will provide another input to deployment decisions.

The architecture should eventually look like:

`
Market Regime Engine
          │
          │
          ▼
     ┌───────────┐
     │           │
     │  Scores   │
     │           │
     └─────┬─────┘
           │
           ▼
Deployment Priority Score
           │
           ▼
Deployment Engine
```

Importantly, the Score Engine and Deployment Priority Score are separate architectural concepts.

The Score Engine is the broader scoring framework.

The Deployment Priority Score is a specific deployment-oriented output that can consume information from that framework.

----

## 6. Target-Weight Drift Engine



## 7. Analytics Engine



## 8. CycleGuard Rules Engine




## 9. CycleGuard Score Engine


## 10. Streamlit Dashboard




----

## Regime

A regime says:

>"Given the current market environment, should CycleGuard temporarily use a different set of bucket targets?"

---

## Drift Analysis

In CycleGuard, drift analysis is the mechanism that answers:

>“Where is my portfolio actually positioned right now compared with where the portfolio is supposed to be?”

It is a critical bridge between your portfolio configuration and the trading/rebalancing decisions CycleGuard eventually makes.

The fundamental calculation is:

Drift = Actual Weight − Target Weight

So:

* +4% means 4 percentage points overweight
* −2% means 2 percentage points underweight
* 0% means exactly on target

---
## Why CycleGuard needs drift analysis

Without drift analysis, CycleGuard knows:

>“My portfolio should have these target weights.”

But it doesn't know:

>“How far have I moved away from those targets?”

That distinction is extremely important.

Your portfolio changes every day because of:

* market movements
* dividends
* interest
* contributions
* withdrawals
* trades
* different securities moving at different rates

You don't have to trade for the portfolio to drift.

For example, suppose you start with:

FZROX = 15% target

Then FZROX rises substantially while bonds and cash don't.

You might end up with:

FZROX = 19% actual

Nothing was necessarily "wrong" with FZROX.

But CycleGuard now knows:

FZROX drift = +4 percentage points

That may eventually trigger a rebalance.


---

## Signals

The signal stack is the part of CycleGuard that answers:

>“What is the market doing right now, and how trustworthy is that move?”

It does not immediately tell CycleGuard to buy or sell a particular ticker. Instead, it collects several independent measurements of market health, combines them, and produces a regime classification:

Defensive → Transition → Risk-On


1. 📈 Trend (Primary) — "Is the market going up or down?"

Use broad market proxy:

* SPDR S&P 500 ETF Trust

Rules:

* Bullish: Price > 200DMA
* Neutral: Price between 50DMA and 200DMA
* Bearish: Price < 200DMA



2. 📊 Breadth (Confirmation) — "How many stocks are participating?"

Use:

* % of stocks above 50DMA

Thresholds:

* Strong: > 65%
* Improving: 50–65%
* Weak: < 50%



3. 🌪 Volatility (Risk Filter) — "How much stress is in the market?"

Use:

* CBOE Volatility Index

Thresholds:

* Calm: < 18
* Neutral: 18–25
* Risk-off: > 25


4. 🚀 Leadership (Your edge) — "Are the right parts of the market leading?"

Track:

* VanEck Semiconductor ETF
* Invesco QQQ Trust

Rules:

* Strong: Above 50DMA
* Weak: Below 50DMA


5. 🔹 Credit — "Are investors willing to take risk?"

Use:

* JNK — SPDR Bloomberg High Yield Bond ETF
* SHY — iShares 1–3 Year Treasury Bond ETF

It uses their prices, their 50-day moving averages, and the JNK/SHY price ratio.


Rules

>JNK/SHY above its 50-day ratio → Healthy; 
otherwise → Stressed.


The really important concept

The signal stack isn't five independent decisions.

It's five pieces of evidence describing the same market environment from different angles.

Think of it like diagnosing a car.

Trend

> Is the car moving forward?

Breadth

> Are all four wheels moving?

Volatility

> Is the engine vibrating?

Credit

> Is the transmission behaving normally?

Leadership

Is the car accelerating?

One measurement isn't enough.

---

## Environment

If you are just running the code locally on your machine, you don't have to do anything. It will automatically default to dev and use dev.yaml.

If you want to run your tests, your test suite (or you) can set the environment variable right before running the code so it uses test.yaml:


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

    psql -h localhost -p 5432 -U postgres -d cycleguard

means "connect to the PostgreSQL database named cycleguard running on this computer, on port 5432, using the PostgreSQL user postgres."

Here's each piece:

|Part|Meaning|
|psql|PostgreSQL's command-line client|
|-h localhost|Connect to PostgreSQL on this computer|
|-p 5432|Connect using PostgreSQL port 5432|
|-U postgres|Connect as PostgreSQL user postgres|
|-d cycleguard|Connect to the database named cycleguard|








Useful commands once connected:
* List all tables: \dt
* Inspect table schema (e.g., positions): \d positions
* Run a query: SELECT * FROM snapshots;
* Exit: 
```
cycleguard-> \q
```

To access the database via psql, you need to use the -U flag to specify the username, -d to specify the database name, and -p to specify the port number.

```
    psql -p 5433 -U cycleguard_user -d cycleguard
    Password: When prompted, enter Wilhelmina1364Rise

    WARNING: Console code page (437) differs from Windows code page (1252)
            8-bit characters might not work correctly. See psql reference
            page "Notes for Windows users" for details.
    Type "help" for help.

    cycleguard=>

```

Use pg_dump with the --schema-only option. This exports the complete database structure—tables, columns, constraints, indexes, sequences, views, functions, etc.—without exporting the actual table data.

```

    pg_dump -h localhost -p 5433 -U cycleguard_user -d cycleguard --schema-only --file=E:\CycleGuard\src\database\cycleguard_schema.sql

```


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
*pytest -x -vv
* pytest -x tests/repositories/test_account_repository.py -vv
* pytest -x tests/repositories/test_import_history_repository.py -vv
* pytest -x tests/repositories/test_positions_repository.py -vv
* pytest -x tests/repositories/test_security_repository.py -vv
* pytest -x tests/repositories/test_snapshot_repository.py -vv
* pytest -x tests/repositories/test_transaction_repository.py -vv

* pytest -x tests/config/test_schema_validator.py -vv
* pytest -x tests/config/test_config_manager.py -vv
* pytest -x tests/config/test_config_loader.py -vv

* pytest -x tests/ingestion/common/test_cli_ingestion_helper.py -vv

* pytest -x tests/services/test_positions_ingestion_service.py -vv
* pytest -x tests/services/test_transactions_ingestion_service.py -vv
* pytest -x tests/services/test_import_rollback_service.py -vv
* pytest -x tests/services/test_import_audit_service.py -vv
* pytest -x tests/services/test_base_ingestion_service.py -vv

* pytest -x tests/database/test_transaction_manager.py -vv

pytest -x -q tests/integration/services/test_transactions_ingestion_integration.py::test_transactions_ingestion_end_to_end

---





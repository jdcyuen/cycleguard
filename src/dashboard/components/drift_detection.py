
"""
Component: Database-Driven Drift Detection Dashboard
====================================================

Purpose
-------
Display portfolio position and bucket allocation drift using the latest
snapshot already stored in the CycleGuard database.

Responsibilities
----------------
1. Resolve database accounts to YAML account configurations by account number.
2. Allow the user to select an account and refresh its drift analysis.
3. Retrieve the latest stored snapshot without importing a CSV or creating
   a new snapshot.
4. Evaluate position and bucket drift through DriftDetectionService.
5. Display results in AG Grid, with position and bucket rows clearly distinct.
6. Warn about missing snapshots and snapshots older than one calendar day.

Architecture
------------
- This module owns Streamlit presentation and user interaction.
- AccountConfigLoader resolves YAML configurations.
- AccountRepository and SnapshotRepository provide database account/snapshot
  access.
- PortfolioAggregationService supplies portfolio and bucket calculations.
- DriftDetectionService evaluates drift and delegates bucket trim proposals
  to BucketTrimProposalService.
- Business calculations and proposal rules remain outside this UI component.

Inputs
------
db_connection:
    Existing raw database connection used by the dashboard repositories.
account_repository:
    Repository that provides the database account list.
snapshot_repository:
    Repository that retrieves the latest snapshot for a database account.

Output
------
Renders the Drift Detection panel in Streamlit. This function does not return
portfolio data and does not create or import snapshots.

Error Handling
--------------
Expected missing configurations and snapshots are reported in the UI.
Unexpected failures are logged with tracebacks and shown as a concise error
message. Exceptions are not silently swallowed.

Logging
-------
Uses Python's standard logging module. Logging configuration is owned by the
application entry point, not this component.

Maintenance Notes
-----------------
Keep this component focused on presentation and orchestration. Put business
rules in service classes, database access in repositories, and account
configuration in YAML. Avoid duplicating calculations performed by services.
"""

from __future__ import annotations

from src.core.logger import get_logger
from datetime import date, datetime
from typing import Any

import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode

from config.account_config_loader import AccountConfigLoader
from repositories.account_repo import AccountRepository
from repositories.snapshot_repo import SnapshotRepository
from repositories.position_repo import PositionRepository
from services.drift_detection_service import DriftDetectionService
from services.portfolio_aggregation_service import PortfolioAggregationService


logger = get_logger(__name__)

STALE_SNAPSHOT_DAYS = 1
GRID_HEIGHT = 520


def _normalize_account_number(value: Any) -> str:
    """Normalize account numbers for YAML-to-database matching."""
    if value is None:
        return ""
    return "".join(str(value).split()).strip()


def _get_account_number(account: Any) -> str:
    """Return an account number from a database account object."""
    return _normalize_account_number(
        getattr(account, "account_number", None)
    )


def _get_snapshot_date(snapshot: Any) -> date | None:
    """Extract a date from a snapshot object, if available."""
    if snapshot is None:
        return None

    value = getattr(snapshot, "snapshot_date", None)
    if value is None:
        return None

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    if isinstance(value, str):
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            logger.warning(
                "Unable to parse snapshot date value: %r",
                value,
            )
            return None

    logger.warning(
        "Unsupported snapshot date type: %s",
        type(value).__name__,
    )
    return None


def _snapshot_age_days(snapshot_date: date) -> int:
    """Return snapshot age in calendar days."""
    return (date.today() - snapshot_date).days


def _format_currency(value: Any) -> str:
    """Format a numeric value as currency, or show unavailable."""
    if value is None or pd.isna(value):
        return "—"

    try:
        return f"${float(value):,.2f}"
    except (TypeError, ValueError):
        return "—"


def _format_percent(value: Any) -> str:
    """Format a numeric value as a percentage, or show unavailable."""
    if value is None or pd.isna(value):
        return "—"

    try:
        return f"{float(value):.2%}"
    except (TypeError, ValueError):
        return "—"


def _build_grid(rows: list[dict[str, Any]], account_id: Any) -> None:
    """Render position and bucket rows in AG Grid."""
    if not rows:
        st.info("No drift rows are available for this snapshot.")
        return

    dataframe = pd.DataFrame(rows)
    logger.info(
        "Drift grid value diagnostics: %s",
        {
            column: [
                (repr(value), type(value).__name__)
                for value in dataframe[column].head(3)
            ]
            for column in ("Market Value", "Actual %")
            if column in dataframe.columns
        },
    )
    display_columns = [
        "Position",
        "Bucket",
        "Market Value",
        "Actual %",
        "Target %",
        "Drift %",
        "Drift $",
        "Status",
        "Proposed Action",
        "Proposed Amount",
    ]

    for column in display_columns:
        if column not in dataframe.columns:
            dataframe[column] = None

    dataframe = dataframe[
		display_columns + ["Row Type"]
	]
    numeric_columns = [
        "Market Value",
        "Actual %",
        "Target %",
        "Drift %",
        "Drift $",
        "Proposed Amount",
    ]

    for column in numeric_columns:
        dataframe[column] = pd.to_numeric(
            dataframe[column].map(
                lambda value: float(value)
                if value is not None and pd.notna(value)
                else None
            ),
            errors="coerce",
        )

    builder = GridOptionsBuilder.from_dataframe(dataframe)
    builder.configure_default_column(
        editable=False,
        sortable=True,
        filter=True,
        resizable=True,
        wrapText=False,
        autoHeight=False,
    )
	
    builder.configure_column(
        "Position",
        width=240,
        minWidth=240,
    )
    builder.configure_column("Bucket", width=160, minWidth=160)

    # Dollar values: preserve the underlying Decimal values.
    builder.configure_column(
        "Market Value",
        type=["numericColumn"],
		valueFormatter=JsCode("""
			function(params) {
				const value = params.value;
                const numericValue = Number(value);
                return value == null || !Number.isFinite(numericValue)
                    ? '-'
					: '$' + Number(value).toLocaleString('en-US', {
						minimumFractionDigits: 2,
						maximumFractionDigits: 2
					});
			}
		"""),
    )
    builder.configure_column(
        "Drift $",
        type=["numericColumn"],
		valueFormatter=JsCode("""
			function(params) {
				const value = params.value;
				const numericValue = Number(value);
				return value == null || !Number.isFinite(numericValue)
					? '-'
					: '$' + Number(value).toLocaleString('en-US', {
						minimumFractionDigits: 2,
						maximumFractionDigits: 2
					});
			}
		"""),
    )
    builder.configure_column(
        "Proposed Amount",
        type=["numericColumn"],
		valueFormatter=JsCode("""
			function(params) {
				const value = params.value;
                const numericValue = Number(value);
                return value == null || !Number.isFinite(numericValue)
                    ? '-'
					: '$' + Number(value).toLocaleString('en-US', {
						minimumFractionDigits: 2,
						maximumFractionDigits: 2
					});
			}
		"""),
    )

    # Weight and drift values are decimal fractions:
    # 0.05 displays as 5.00%.
    builder.configure_column(
        "Actual %",
        type=["numericColumn"],
		valueFormatter=JsCode("""
			function(params) {
				const value = params.value;
                const numericValue = Number(value);
                return value == null || !Number.isFinite(numericValue)
                    ? '-'
					: (Number(value) * 100).toFixed(2) + '%';
			}
		"""),
    )
    builder.configure_column(
        "Target %",
        type=["numericColumn"],
		valueFormatter=JsCode("""
			function(params) {
				const value = params.value;
                const numericValue = Number(value);
                return value == null || !Number.isFinite(numericValue)
                    ? '-'
					: (Number(value) * 100).toFixed(2) + '%';
			}
		"""),
    )
    builder.configure_column(
        "Drift %",
        type=["numericColumn"],
		valueFormatter=JsCode("""
			function(params) {
				const value = params.value;
                const numericValue = Number(value);
                return value == null || !Number.isFinite(numericValue)
                    ? '-'
					: (Number(value) * 100).toFixed(2) + '%';
			}
		"""),

    )

    builder.configure_column("Status", minWidth=165)
    builder.configure_column("Proposed Action", minWidth=150)
    builder.configure_column("Proposed Amount", minWidth=145)

    builder.configure_grid_options(
        domLayout="normal",
        rowHeight=36,
        headerHeight=40,
        getRowStyle=JsCode("""
            function(params) {
                if (
                    params.data &&
                    params.data['Row Type'] === 'Bucket'
                ) {
                    return {
                        fontWeight: 'bold',
                        backgroundColor: '#E8EEF7'
                    };
                }
                return {};
            }
        """),
    )

    grid_options = builder.build()

    logger.debug(
        "Rendering drift grid for account_id=%s with %d rows",
        account_id,
        len(dataframe),
    )

    AgGrid(
        dataframe,
        gridOptions=grid_options,
        height=GRID_HEIGHT,
        update_mode=GridUpdateMode.NO_UPDATE,
        allow_unsafe_jscode=True,
        fit_columns_on_grid_load=False,
        key=f"drift_detection_grid_{account_id}",
    )


def _load_account_configurations() -> list[Any]:
    """Load YAML configurations and report configuration failures."""
    try:
        configurations = AccountConfigLoader().load()
    except Exception:
        logger.exception("Unable to load account YAML configurations")
        raise

    if not configurations:
        logger.warning("No account YAML configurations were loaded")

    return configurations


def _match_accounts_to_configurations(
    database_accounts: list[Any],
    configurations: list[Any],
) -> list[tuple[Any, Any]]:
    """Match database accounts to YAML configurations by account number."""
    configs_by_number = {
        _normalize_account_number(getattr(config, "account_number", None)): config
        for config in configurations
        if _normalize_account_number(
            getattr(config, "account_number", None)
        )
    }

    matches: list[tuple[Any, Any]] = []

    for database_account in database_accounts:
        account_number = _get_account_number(database_account)

        if not account_number:
            logger.warning(
                "Database account id=%s has no account number",
                getattr(database_account, "id", None),
            )
            continue

        configuration = configs_by_number.get(account_number)

        if configuration is None:
            logger.warning(
                "No YAML configuration matches database account id=%s",
                getattr(database_account, "id", None),
            )
            continue

        matches.append((database_account, configuration))

    return matches


def _evaluate_snapshot_drift(
    db_connection: Any,
    account_config: Any,
    snapshot_id: int,
) -> list[dict[str, Any]]:
    """Build services and evaluate drift for an existing snapshot."""
    position_repository = PositionRepository(db_connection)
    portfolio_service = PortfolioAggregationService(
        position_repository,
        account_config,
    )
    drift_service = DriftDetectionService(
        portfolio_service,
        account_config,
    )

    logger.info(
        "Evaluating drift for account=%s snapshot_id=%s",
        getattr(account_config, "name", "unknown"),
        snapshot_id,
    )

    return drift_service.evaluate(snapshot_id)



def render_drift_detection(
    db_connection: Any,
    account_repository: AccountRepository,
    snapshot_repository: SnapshotRepository,
) -> None:
    """
    Render the independent Drift Detection dashboard panel.

    Refreshing this panel reads and evaluates the latest existing database
    snapshot. It does not import Fidelity files or create snapshots.
    """
    with st.container(border=True):
        st.subheader("Drift Detection")
        st.caption(
            "Evaluates the latest stored database snapshot. "
            "This panel does not import or synchronize Fidelity data."
        )

        try:
            configurations = _load_account_configurations()
            database_accounts = account_repository.list_accounts()
            matches = _match_accounts_to_configurations(
                database_accounts,
                configurations,
            )
        except Exception:
            logger.exception(
                "Unable to initialize the Drift Detection panel"
            )
            st.error(
                "Drift Detection could not load account information. "
                "Check the application logs for details."
            )
            return

        if not matches:
            st.warning(
                "No database accounts match an account_number in the YAML "
                "account configurations. Check the account configuration files."
            )
            return

        labels: dict[str, tuple[Any, Any]] = {}

        for database_account, account_config in matches:
            display_name = (
                getattr(account_config, "display_name", None)
                or getattr(account_config, "name", None)
                or getattr(database_account, "name", None)
                or "Account"
            )
            account_number = _get_account_number(database_account)
            label = f"{display_name} ({account_number})"

            # Avoid ambiguous selectbox labels if duplicate display names exist.
            if label in labels:
                label = (
                    f"{label} - DB ID "
                    f"{getattr(database_account, 'id', 'unknown')}"
                )

            labels[label] = (database_account, account_config)

        selected_label = st.selectbox(
            "Account",
            options=list(labels.keys()),
            key="drift_detection_account_selector",
        )
        database_account, account_config = labels[selected_label]
        account_id = getattr(database_account, "id", None)

        refresh_clicked = st.button(
            "Refresh Drift",
            key="refresh_drift_detection",
            help=(
                "Re-evaluate drift using the latest snapshot "
                "already stored in the database."
            ),
        )

        if refresh_clicked:
            logger.info(
                "Manual drift refresh requested for database account id=%s",
                account_id,
            )

        try:
            snapshot = snapshot_repository.get_latest_by_account(account_id)
        except Exception:
            logger.exception(
                "Unable to retrieve latest snapshot for account_id=%s",
                account_id,
            )
            st.error(
                "Unable to retrieve the latest snapshot. "
                "Check the application logs for details."
            )
            return

        if snapshot is None:
            logger.info(
                "No snapshot exists for database account id=%s",
                account_id,
            )
            st.warning(
                "No database snapshot exists for this account. "
                "Import a portfolio snapshot through the existing ingestion "
                "workflow before evaluating drift."
            )
            return

        snapshot_id = getattr(snapshot, "id", None)
        snapshot_date = _get_snapshot_date(snapshot)

        if snapshot_id is None:
            logger.error(
                "Latest snapshot for account_id=%s has no snapshot id",
                account_id,
            )
            st.error(
                "The latest snapshot record is missing its identifier. "
                "Check the database and application logs."
            )
            return

        if snapshot_date is None:
            st.warning(
                "The latest snapshot date is missing or invalid. "
                "Drift can still be evaluated, but snapshot freshness is unknown."
            )
        else:
            age_days = _snapshot_age_days(snapshot_date)
            st.caption(
                f"Snapshot date: {snapshot_date.isoformat()} | "
                f"Age: {age_days} calendar day(s)"
            )

            if age_days > STALE_SNAPSHOT_DAYS:
                logger.warning(
                    "Snapshot is stale for account_id=%s: date=%s age_days=%s",
                    account_id,
                    snapshot_date,
                    age_days,
                )
                st.warning(
                    f"This snapshot is {age_days} calendar days old. "
                    "Results are shown for the latest available snapshot; "
                    "refreshing drift does not import newer data."
                )

        try:
            with st.spinner("Evaluating portfolio drift..."):
                rows = _evaluate_snapshot_drift(
                    db_connection,
                    account_config,
                    snapshot_id,
                )
        except ValueError as exc:
            logger.warning(
                "Drift evaluation validation failed for account_id=%s "
                "snapshot_id=%s: %s",
                account_id,
                snapshot_id,
                exc,
                exc_info=True,
            )
            st.error(
                "Drift evaluation could not complete because portfolio "
                "validation failed. Review account YAML bucket mappings, "
                "targets, and the application logs."
            )
            return
        except Exception:
            logger.exception(
                "Unexpected drift evaluation failure for account_id=%s "
                "snapshot_id=%s",
                account_id,
                snapshot_id,
            )
            st.error(
                "Drift evaluation failed unexpectedly. "
                "Check the application logs for details."
            )
            return

        if not rows:
            st.info("The latest snapshot contains no rows to evaluate.")
            return

        dataframe = pd.DataFrame(rows)
        position_rows = dataframe[dataframe["Row Type"] == "Position"]
        bucket_rows = dataframe[dataframe["Row Type"] == "Bucket"]

        col1, col2, col3 = st.columns(3)
        col1.metric("Positions", len(position_rows))
        col2.metric("Buckets", len(bucket_rows))

        trim_rows = bucket_rows[
            bucket_rows["Proposed Action"].fillna("").str.contains(
                "trim",
                case=False,
                regex=False,
            )
        ]
        col3.metric("Bucket Trim Proposals", len(trim_rows))

        _build_grid(rows, account_id)

        no_target_rows = position_rows[
            position_rows["Status"].fillna("").eq("No target configured")
        ]
        if not no_target_rows.empty:
            st.info(
                f"{len(no_target_rows)} position(s) have no configured target. "
                "Their target and drift values remain unavailable; no target "
                "has been inferred."
            )

        underweight_rows = dataframe[
            dataframe["Status"].fillna("").str.contains(
                "underweight",
                case=False,
                regex=False,
            )
        ]
        if not underweight_rows.empty:
            st.caption(
                "Underweight positions or buckets are informational; "
                "underweight status does not automatically generate buy orders."
            )

        if not trim_rows.empty:
            total_proposed_trim = pd.to_numeric(
                trim_rows["Proposed Amount"],
                errors="coerce",
            ).fillna(0).sum()

            st.info(
                "Bucket trim proposals are provided by the existing "
                "BucketTrimProposalService. "
                f"Total proposed bucket trims: "
                f"{_format_currency(total_proposed_trim)}. "
                "Position rows do not duplicate bucket trim amounts."
            )

        logger.info(
            "Drift Detection rendered for account_id=%s snapshot_id=%s "
            "positions=%s buckets=%s",
            account_id,
            snapshot_id,
            len(position_rows),
            len(bucket_rows),
        )

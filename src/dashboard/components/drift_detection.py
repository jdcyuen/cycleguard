
"""
Component: Database-Driven Drift Detection Dashboard
====================================================

Purpose
-------
Display portfolio position and bucket allocation drift using the latest
snapshot already stored in the CycleGuard database.

Responsibilities
----------------
1. Resolve database accounts to YAML account configurations through the
   shared DriftDetectionOrchestrationService.
2. Allow the user to select an account and refresh its drift analysis.
3. Evaluate the latest stored database snapshot without importing a CSV
   or creating a new snapshot.
4. Display position and bucket drift results in AG Grid.
5. Warn about missing snapshots and snapshots older than one calendar day.

Architecture
------------
- This module owns Streamlit presentation and user interaction.
- DriftDetectionOrchestrationService coordinates account matching, snapshot
  retrieval, portfolio aggregation, and drift evaluation.
- AccountRepository and SnapshotRepository provide database access to the
  orchestration service.
- Business calculations and proposal rules remain in the service layer.

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

from core.logger import get_logger
from datetime import date, datetime
from typing import Any

import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode
from repositories.account_repo import AccountRepository
from repositories.snapshot_repo import SnapshotRepository
from services.drift_detection_orchestration_service import (
    DriftDetectionOrchestrationService,
)
from services.account_reconciliation_service import (
    AccountReconciliationService,
    AccountReconciliationServiceError,
    normalize_account_number,
)
from services.account_registration_service import (
    AccountRegistrationService,
    AccountRegistrationError,
    AccountRegistrationValidationError,
    AccountRegistrationConflictError,
)

logger = get_logger(__name__)

STALE_SNAPSHOT_DAYS = 1
GRID_HEIGHT = 520


def _normalize_account_number(value: Any) -> str:
    """Use the shared account-number normalization rule."""
    return normalize_account_number(value)


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
	
def _render_pending_account_registration(
    pending_accounts: list[Any],
    account_repository: AccountRepository,
) -> None:
    """Prompt once to register all pending YAML accounts."""

    success_message = st.session_state.pop(
        "account_registration_success",
        None,
    )
    if success_message:
        st.success(success_message)

    if st.session_state.pop(
        "suppress_account_registration_dialog_once",
        False,
    ):
        return

    if not pending_accounts:
        return

    @st.dialog("Unregistered Accounts")
    def confirm_registration() -> None:
        st.write(
            "The following accounts have YAML configurations "
            "but are not registered in CycleGuard:"
        )

        for account_config in pending_accounts:
            display_name = (
                getattr(account_config, "display_name", None)
                or "Unnamed Account"
            )
            account_number = normalize_account_number(
                getattr(account_config, "account_number", None)
            )
            st.write(f"- **{display_name}** (`{account_number}`)")

        st.write(
            f"Would you like to register all "
            f"{len(pending_accounts)} account(s)?"
        )

        col_yes, col_no = st.columns(2)

        with col_yes:
            if st.button(
                "Yes, register all",
                type="primary",
                use_container_width=True,
                key="confirm_register_all_accounts",
            ):
                registration_service = AccountRegistrationService(
                    account_repository
                )

                successful = []
                failed = []

                for account_config in pending_accounts:
                    display_name = (
                        getattr(account_config, "display_name", None)
                        or "Unnamed Account"
                    )

                    try:
                        registration_service.register(account_config)
                        successful.append(display_name)

                    except AccountRegistrationError as exc:
                        logger.warning(
                            "Account registration rejected for %s: %s",
                            display_name,
                            exc,
                        )
                        failed.append(f"{display_name}: {exc}")

                    except Exception:
                        logger.exception(
                            "Unexpected registration failure for %s",
                            display_name,
                        )
                        failed.append(
                            f"{display_name}: Unexpected error. "
                            "Check application logs."
                        )

                messages = []

                if successful:
                    messages.append(
                        "Successfully registered: "
                        + ", ".join(successful)
                    )

                if failed:
                    messages.append(
                        "Registration failures: "
                        + "; ".join(failed)
                    )

                st.session_state["account_registration_success"] = (
                    " | ".join(messages)
                )
                st.rerun()

        with col_no:
            if st.button(
                "No",
                use_container_width=True,
                key="cancel_register_all_accounts",
            ):
                st.session_state[
                    "suppress_account_registration_dialog_once"
                ] = True
                st.rerun()

    confirm_registration()

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
            reconciliation_service = AccountReconciliationService(
                account_repository
            )
            reconciliation = reconciliation_service.reconcile()

            orchestration_service = DriftDetectionOrchestrationService(
                db_connection,
                account_repository,
                snapshot_repository,
            )

            matches = [
                (match.database_account, match.account_config)
                for match in reconciliation.active_accounts
            ]

        except AccountReconciliationServiceError as exc:
            logger.exception(
                "Account reconciliation failed in Drift Detection"
            )
            st.error(
                f"Account reconciliation failed: {exc}"
            )
            return
        except Exception:
            logger.exception(
                "Unable to initialize the Drift Detection panel"
            )
            st.error(
                "Drift Detection could not load account information. "
                "Check the application logs for details."
            )
            return			

        if reconciliation.historical_accounts:
            st.caption(
                f"{len(reconciliation.historical_accounts)} historical/inactive "
                "database account(s) have no matching YAML configuration."
            )

        if reconciliation.duplicate_accounts:
            st.error(
                f"{len(reconciliation.duplicate_accounts)} duplicate account "
                "group(s) detected. These accounts are excluded from Drift Detection."
            )
            for duplicate in reconciliation.duplicate_accounts:
                st.warning(
                    f"Duplicate account number: "
                    f"{duplicate.normalized_account_number} "
                    f"(source: {duplicate.source}, "
                    f"records: {len(duplicate.records)})"
                )

        _render_pending_account_registration(
            reconciliation.pending_registration,
            account_repository,
        )
		
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

        dropdown_width = max(
            200,
            max(len(label) for label in labels) * 8 + 48,
        )

        selected_label = st.selectbox(
            "Account",
            options=list(labels.keys()),
            key="drift_detection_account_selector",
            width=dropdown_width,
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
            with st.spinner("Evaluating portfolio drift..."):
                result = orchestration_service.evaluate_account(
                    database_account,
                    account_config,
                )
        except ValueError as exc:
            logger.warning(
                "Drift evaluation validation failed for account_id=%s: %s",
                account_id,
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
                "Unexpected drift evaluation failure for account_id=%s",
                account_id,
            )
            st.error(
                "Drift evaluation failed unexpectedly. "
                "Check the application logs for details."
            )
            return

        snapshot = result.snapshot

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

        snapshot_date = _get_snapshot_date(snapshot)

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

        rows = result.rows

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

        snapshot_id = getattr(snapshot, "id", None)
        logger.info(
            "Drift Detection rendered for account_id=%s snapshot_id=%s "
            "positions=%s buckets=%s",
            account_id,
            snapshot_id,
            len(position_rows),
            len(bucket_rows),
        )

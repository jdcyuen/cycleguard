
"""
Standalone Drift Detection Dashboard
====================================

Purpose
-------
Run the database-driven Drift Detection component independently of the
main CycleGuard dashboard.

Usage
-----
streamlit run src/dashboard/drift_detection_app.py

Architecture
------------
Reuses the existing Drift Detection presentation component and shared
orchestration service. Account matching, snapshot retrieval, and drift
calculations are not duplicated here.

Data Safety
-----------
Read-only with respect to portfolio data. This application evaluates
existing database snapshots; it does not import Fidelity files, create
snapshots, or execute trades.
"""

from __future__ import annotations

import streamlit as st

from core.logger import setup_logging
from database.connection import DBConnection
from repositories.account_repo import AccountRepository
from repositories.snapshot_repo import SnapshotRepository
from dashboard.components.drift_detection import render_drift_detection


@st.cache_resource
def get_database_resources():
    """Create and cache the database wrapper and raw connection."""
    db_connection = DBConnection()
    connection = db_connection.connect()

    if connection is None:
        raise RuntimeError("DBConnection.connect() returned None.")

    return db_connection, connection


def main() -> None:
    """Render the standalone Drift Detection application."""
    st.set_page_config(
        page_title="CycleGuard - Drift Detection",
        page_icon="📊",
        layout="wide",
    )

    setup_logging()

    st.title("CycleGuard — Drift Detection")
    st.caption(
        "Read-only analysis of portfolio drift using the latest "
        "snapshot already stored in the database."
    )

    try:
        _, connection = get_database_resources()

        account_repository = AccountRepository(connection)
        snapshot_repository = SnapshotRepository(connection)

        render_drift_detection(
            connection,
            account_repository,
            snapshot_repository,
        )

    except Exception as exc:
        st.exception(exc)


if __name__ == "__main__":
    main()

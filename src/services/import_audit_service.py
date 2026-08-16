from models.import_audit import (
    ImportAuditStatus,
    ImportAuditResult,
)


class ImportAuditService:
    """
    Audits the database records created by an import.

    The audit compares the import history record against the
    actual positions or transactions associated with that import.
    """

    def __init__(
        self,
        import_history_repository,
        position_repository,
        transaction_repository,
        snapshot_repository,
    ):
        self.import_history_repository = import_history_repository
        self.position_repository = position_repository
        self.transaction_repository = transaction_repository
        self.snapshot_repository = snapshot_repository

    def audit(
        self,
        import_id: int,
    ) -> ImportAuditResult:
        """
        Audit a completed import.

        Returns PASS when the records associated with the import
        are consistent with the import history record.

        Returns FAIL when the import cannot be found or the
        imported row counts do not match.
        """

        # ---------------------------------------------------------
        # 1. Retrieve import history
        # ---------------------------------------------------------

        import_history = (
            self.import_history_repository.get_by_id(import_id)
        )

        if import_history is None:
            return ImportAuditResult(
                import_id=import_id,
                status=ImportAuditStatus.FAIL,
                message=(
                    f"Import history not found: {import_id}"
                ),
            )

        # ---------------------------------------------------------
        # 2. Audit positions import
        # ---------------------------------------------------------

        if import_history.import_type == "positions":

            actual_count = (
                self.position_repository
                .count_by_import_history_id(import_id)
            )

            expected_count = import_history.rows_imported

            if actual_count != expected_count:
                return ImportAuditResult(
                    import_id=import_id,
                    status=ImportAuditStatus.FAIL,
                    message=(
                        "Position count mismatch: "
                        f"expected {expected_count}, "
                        f"found {actual_count}."
                    ),
                )

            # -----------------------------------------------------
            # 3. Verify snapshot exists for positions import
            # -----------------------------------------------------

            if import_history.snapshot_date is not None:

                snapshot = (
                    self.snapshot_repository.get_by_date(
                        import_history.snapshot_date
                    )
                )

                if snapshot is None:
                    return ImportAuditResult(
                        import_id=import_id,
                        status=ImportAuditStatus.FAIL,
                        message=(
                            "Snapshot not found for "
                            f"snapshot_date="
                            f"{import_history.snapshot_date}."
                        ),
                    )

            return ImportAuditResult(
                import_id=import_id,
                status=ImportAuditStatus.PASS,
                message=(
                    "Position import audit passed. "
                    f"{actual_count} positions verified."
                ),
            )

        # ---------------------------------------------------------
        # 4. Audit transactions import
        # ---------------------------------------------------------

        if import_history.import_type == "transactions":

            actual_count = (
                self.transaction_repository
                .count_by_import_history_id(import_id)
            )

            expected_count = import_history.rows_imported

            if actual_count != expected_count:
                return ImportAuditResult(
                    import_id=import_id,
                    status=ImportAuditStatus.FAIL,
                    message=(
                        "Transaction count mismatch: "
                        f"expected {expected_count}, "
                        f"found {actual_count}."
                    ),
                )

            return ImportAuditResult(
                import_id=import_id,
                status=ImportAuditStatus.PASS,
                message=(
                    "Transaction import audit passed. "
                    f"{actual_count} transactions verified."
                ),
            )

        # ---------------------------------------------------------
        # 5. Unknown import type
        # ---------------------------------------------------------

        return ImportAuditResult(
            import_id=import_id,
            status=ImportAuditStatus.FAIL,
            message=(
                f"Unsupported import type: "
                f"{import_history.import_type}"
            ),
        )

        
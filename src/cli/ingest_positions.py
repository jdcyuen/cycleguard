import argparse

from ingestion.common.cli_ingest_helper import (
    confirm_import,
    display_results,
    resolve_account,
    resolve_snapshot_date,
)

from services.positions_ingestion_service import (
    PositionsIngestionService,
)


def parse_args():

    parser = argparse.ArgumentParser(
        description="Import Fidelity positions CSV."
    )

    parser.add_argument(
        "--file",
        required=True,
        help="Positions CSV file."
    )

    parser.add_argument(
        "--account",
        required=False,
        help="Configured account name."
    )

    parser.add_argument(
        "--snapshot-date",
        required=False,
        help=(
            "Snapshot date (YYYY-MM-DD). "
            "Overrides date derived from filename."
        )
    )

    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Prompt before importing."
    )

    return parser.parse_args()


def main():

    args = parse_args()

    account_name = resolve_account(
        args.account
    )

    snapshot_date = resolve_snapshot_date(
        snapshot_date=args.snapshot_date,
        csv_file=args.file,
    )

    if args.confirm:

        if not confirm_import(
            "positions",
            account_name,
        ):
            print(
                "Import cancelled."
            )
            return

    try:

        service = (
            PositionsIngestionService.build()
        )

        result = service.ingest(
            csv_file=args.file,
            account_name=account_name,
            snapshot_date=snapshot_date,
        )

        display_results(
            account_name,
            result,
        )

    except Exception as exc:

        print(
            f"Positions import failed: "
            f"{exc}"
        )

        raise SystemExit(1)


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Read a CSV with two columns (type, id) (with a header row) and for each row where the
first column is 'Journal' call history_records_assemble.history_records_assemble with
the specified arguments.

Usage:
    python build_history.py input.csv

Options:
    --dry-run    Do not actually call the assemble function; just log what would be done.
"""

from __future__ import annotations

import argparse
import csv
import logging
import os
import sys
import datetime
from typing import Tuple

try:
    from portality.scripts import history_records_assemble
except Exception as e:
    history_records_assemble = None  # will raise later if we try to call it


CSV_DIR = "/home/richard/tmp/history.20260127/analyse"
TAR_DIR = "/home/richard/tmp/history.20260127/analyse"
OUT_BASE = "/home/richard/tmp/history.20260127/history_extracts/Journal"


def process_csv(csv_path: str, dry_run: bool = False) -> Tuple[int, int]:
    """Process the CSV and call the assemble function for Journal rows.

    Returns a tuple (processed_count, error_count).
    """
    processed = 0
    errors = 0

    if history_records_assemble is None:
        logging.error("Unable to import portality.scripts.history_records_assemble; aborting")
        return 0, 1

    with open(csv_path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.reader(fh)
        header = next(reader, None)
        for rownum, row in enumerate(reader, start=2):
            if not row:
                logging.debug("Skipping empty row %s", rownum)
                continue
            if len(row) < 2:
                logging.warning("Row %s has fewer than 2 columns, skipping: %r", rownum, row)
                errors += 1
                continue

            typ = row[0].strip()
            doc_id = row[1].strip()
            if not doc_id:
                logging.warning("Row %s has empty id, skipping", rownum)
                errors += 1
                continue

            if typ.lower() != "journal":
                logging.debug("Row %s is type %r; skipping (only Journal rows are processed)", rownum, typ)
                continue

            out_dir = os.path.join(OUT_BASE, doc_id)

            logging.info("Assembling history for Journal id=%s -> out_dir=%s", doc_id, out_dir)

            if dry_run:
                processed += 1
                continue

            try:
                # Call the assemble function with the required keyword args
                history_records_assemble.history_records_assemble(
                    id=doc_id,
                    csv_dir=CSV_DIR,
                    tar_dir=TAR_DIR,
                    out_dir=out_dir,
                    assemble=True,
                    do_diff=False,
                )

                # After assemble completes, remove dated JSON files older than 2026-01-15.
                cutoff = datetime.date(2026, 1, 15)
                try:
                    # Ensure out_dir exists before listing
                    if os.path.isdir(out_dir):
                        for fname in os.listdir(out_dir):
                            # Only consider .json files
                            if not fname.endswith('.json'):
                                continue
                            # Skip files starting with '_' or 'base_'
                            if fname.startswith('_') or fname.startswith('base_'):
                                continue

                            # Filename should begin with YYYY-MM-DD
                            date_part = fname[:10]
                            try:
                                file_date = datetime.datetime.strptime(date_part, "%Y-%m-%d").date()
                            except Exception:
                                logging.debug("Skipping file with non-date prefix: %s", fname)
                                continue

                            if file_date < cutoff:
                                path = os.path.join(out_dir, fname)
                                if dry_run:
                                    logging.info("(dry-run) would remove old file: %s", path)
                                else:
                                    try:
                                        os.remove(path)
                                        logging.info("Removed old file: %s", path)
                                    except Exception:
                                        logging.exception("Failed to remove old file: %s", path)
                    else:
                        logging.debug("Out directory does not exist, skipping cleanup: %s", out_dir)
                except Exception:
                    logging.exception("Unexpected error during cleanup for id %s", doc_id)

                processed += 1
            except Exception:
                logging.exception("Failed to assemble history for id %s (row %s)", doc_id, rownum)
                errors += 1

    return processed, errors


def main(argv=None):
    parser = argparse.ArgumentParser(description="Assemble history for Journal ids from a CSV")
    parser.add_argument("csv", help="Input CSV path (header row will be skipped)")
    parser.add_argument("--dry-run", action="store_true", help="Do not actually call the assemble function")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")

    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

    csv_path = args.csv
    if not os.path.exists(csv_path):
        logging.error("CSV file does not exist: %s", csv_path)
        sys.exit(2)

    processed, errors = process_csv(csv_path, dry_run=args.dry_run)
    logging.info("Done. Processed=%d, Errors=%d", processed, errors)
    if errors:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()

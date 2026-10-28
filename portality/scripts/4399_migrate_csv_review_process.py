"""
S.E. 2026-10-02

Bring the 'Review process' values in publisher update CSVs up to date with the renames made to our data in
portality/migrate/20260501_4232_peer_review_rename, so they can be ingested by journals_update_via_csv.py
https://github.com/DOAJ/doajPM/issues/4399

Each file is rewritten in place, with the original kept alongside as <file>.bak

Usage:
    python 4399_migrate_csv_review_process.py ~/4399_publishercsvs/*.csv
"""

import csv
import shutil

# As per Journal2PublisherUploadQuestionsXwalk.q("review_process")
REVIEW_PROCESS_HEADER = "Review process"

RENAMES = {
    "Anonymous peer review": "Single anonymous peer review",
    "Peer review": "Unspecified peer review"
}


def migrate_value(value):
    processes = []
    for p in [_.strip() for _ in value.split(",")]:
        p = RENAMES.get(p, p)
        if p not in processes:
            processes.append(p)
    return ", ".join(processes)


def migrate_file(path):
    # Open with encoding that deals with the Byte Order Mark since we're given files from Windows.
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))

    try:
        col = rows[0].index(REVIEW_PROCESS_HEADER)
    except (IndexError, ValueError):
        print(f"{path}: no review process column, skipping")
        return

    changed = 0
    for row_ix, row in enumerate(rows[1:], start=2):
        if col >= len(row) or not row[col]:
            continue
        new = migrate_value(row[col])
        if new != row[col]:
            print(f"{path} row {row_ix}: \"{row[col]}\" -> \"{new}\"")
            row[col] = new
            changed += 1

    if changed:
        shutil.copy2(path, path + ".bak")
        with open(path, "w", encoding="utf-8", newline="") as f:
            csv.writer(f).writerows(rows)
    print(f"{path}: {changed} rows updated")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("infiles", nargs="+", help="Paths to publisher update CSVs")
    args = parser.parse_args()

    for p in args.infiles:
        migrate_file(p)

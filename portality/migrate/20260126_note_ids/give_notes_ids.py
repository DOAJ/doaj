#!/usr/bin/env python3
"""
Migration script: give notes ids

Iterates through all Journal and Application records and ensures every note in
`admin.notes` has a non-empty `id` field. If missing or empty, assigns a
new uuid4 hex value and saves the parent record.

Usage:
    python give_notes_ids.py            # runs and updates records, prints summary
    python give_notes_ids.py -n         # dry run, does not save
    python give_notes_ids.py -o out.csv # write a CSV of changes

The script records (record_type, record_id, note_index, new_note_id) for each
note updated.
"""

import csv
import argparse
import uuid
import sys
from copy import deepcopy

from portality import models


def process_model(model_cls, dry_run=False):
    """Iterate all objects of a model class and ensure notes have ids.

    Returns a list of tuples (record_type, record_id, note_index, new_note_id).
    """
    changes = []
    for obj in model_cls.iterate():
        # obj is a model instance
        notes = obj.notes
        if not notes:
            continue
        changed = False
        # ensure notes is a list (some legacy records might have bad shapes)
        if not isinstance(notes, list):
            # attempt to coerce to list
            try:
                notes = list(notes)
            except Exception:
                continue
        for i, note in enumerate(notes):
            # note should be a dict-like
            if not isinstance(note, dict):
                continue
            nid = note.get("id")
            if nid is None or (isinstance(nid, str) and nid.strip() == ""):
                new_id = uuid.uuid4().hex
                # set on the in-memory object
                notes[i]["id"] = new_id
                if not changed:
                    changes.append(obj.id)
                    changed = True
        if changed:
            # set notes back onto the object and save unless dry_run
            try:
                obj.set_notes(notes)
                if not dry_run:
                    obj.save()
            except Exception:
                # log to stderr, but continue
                print(f"Failed to save {model_cls.__name__} {obj.id}", file=sys.stderr)
    return changes


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--dry-run", action="store_true", help="Do not save changes, just report")
    parser.add_argument("-o", "--out", help="CSV output file path to record changes")
    args = parser.parse_args()

    print("Processing Journals...")
    journal_changes = process_model(models.Journal, dry_run=args.dry_run)
    print("Journals updated: ", len(journal_changes))

    print("Processing Applications...")
    app_changes = process_model(models.Application, dry_run=args.dry_run)
    print(f"Applications updated: {len(app_changes)}")

    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(["record_type", "record_id"])
            for r in journal_changes:
                writer.writerow(["Journal", r])
            for r in app_changes:
                writer.writerow(["Application", r])
        print(f"Wrote details to {args.out}")
    else:
        print(journal_changes)
        print(app_changes)


if __name__ == "__main__":
    main()


#!/usr/bin/env python3
"""
Load all JSON files from subfolders of a directory into a list of Python dicts.

Behavior:
- By default the script looks in the immediate subdirectories of the given base
  directory and collects any files ending with '.json'.
- If --recursive is provided, it will walk each subdirectory recursively.
- Invalid JSON files are skipped with a logged warning.
- Optionally write the combined list to an output JSON file with --out-file.

Usage:
    python build_notes.py /path/to/base_dir [--recursive] [--out-file combined.json]
"""

from __future__ import annotations

import argparse
import json, uuid
import logging, csv
import os
from copy import deepcopy
from pathlib import Path
from typing import Any, List
from datetime import datetime

def load_jsons_from_dirs(base_dir: str, out_dir: str, recursive: bool = False):
    """Iterate through folders inside base_dir, find .json files and load them.

    Args:
        base_dir: path to a directory containing subdirectories to scan.
        recursive: if True, walk subdirectories recursively; otherwise only scan
                   the immediate subdirectory level.

    Returns:
        A list of Python objects loaded from the JSON files (usually dicts).
    """

    base = Path(base_dir)

    if not base.exists() or not base.is_dir():
        raise ValueError(f"base_dir does not exist or is not a directory: {base_dir}")

    overall_report = {}

    # Iterate over entries in base_dir and consider directories only
    for entry in sorted(base.iterdir()):

        if not entry.is_dir():
            continue

        records: List[Any] = []

        # Walk this subdirectory
        if recursive:
            walker = entry.rglob("*.json")
        else:
            walker = entry.glob("*.json")

        for json_path in sorted(walker):
            # Ensure it's a file
            if not json_path.is_file():
                continue

            try:
                with json_path.open("r", encoding="utf-8") as fh:
                    obj = json.load(fh)
                obj["__source_file"] = str(json_path)
                records.append(obj)
                logging.debug("Loaded JSON file: %s", str(json_path))
            except Exception as e:
                logging.warning("Skipping file %s due to error: %s", str(json_path), e)
                continue

        notes, report = resolve_notes(records)
        overall_report[entry.name] = report

        out_path = os.path.join(out_dir, entry.name + ".json")
        try:
            with open(out_path, "w", encoding="utf-8") as fh:
                json.dump(notes, fh, indent=2, ensure_ascii=False)
            logging.info("Wrote Notes JSON to %s", str(out_path))
        except Exception as e:
            logging.error("Failed to write out-file %s: %s", str(out_path), e)

    try:
        out_csv_path = os.path.join(out_dir, "overall_report.csv")
        with open(out_csv_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["id", "missing_ids", "missing_notes", "missing_note_data", "missing_id_data", "file_order"])
            for key in sorted(overall_report.keys()):
                rep = overall_report.get(key, {})
                writer.writerow([key,
                                 rep.get("missing_ids", 0),
                                 rep.get("missing_notes", 0),
                                 json.dumps(rep.get("missing_note_data", []), indent=2),
                                 json.dumps(rep.get("missing_id_data", []), indent=2),
                                 json.dumps(rep.get("ordered_record_files", []), indent=2)
                                 ])
        logging.info("Wrote overall report CSV to %s", out_csv_path)
    except Exception as e:
        logging.error("Failed to write overall report CSV %s: %s", str(out_dir), e)


def resolve_notes(candidates):
    def _key(item):
        v = item.get("last_updated") if isinstance(item, dict) else getattr(item, "last_updated", None)
        if v is None:
            v = item.get("last_manual_update") if isinstance(item, dict) else getattr(item, "last_manual_update", None)

        return v

    candidates.sort(key=_key)

    def _already_seen(note, with_ids, without_ids):
        nid = note.get("id")
        if nid != "" and nid is not None:
            for n in with_ids:
                if n.get("id") == nid:
                    return True
            for n in without_ids:
                if n.get("note") == note.get("note"):
                    return True

        else:
            for n in without_ids:
                if n.get("note") == note.get("note"):
                    return True

        return False

    def _detect_missing(notes, with_ids, without_ids, all_missing):
        missing = []
        for note in with_ids:
            found = False
            nid = note.get("id")
            for n in notes:
                if n.get("id") == nid:
                    found = True
            if not found:
                missing.append(deepcopy(note))

        for note in without_ids:
            found = False
            ntext = note.get("note")
            for n in notes:
                if n.get("note") == ntext:
                    found = True
            if not found:
                missing.append(deepcopy(note))

        new_missing = []
        for m in missing:
            mid = m.get("id")
            mtext = m.get("note")
            already = False
            if mid not in (None, ""):
                for am in all_missing:
                    if am.get("id") == mid:
                        already = True
                        break
            else:
                for am in all_missing:
                    if am.get("note") == mtext:
                        already = True
                        break
            if not already:
                new_missing.append(m)
        missing = new_missing
        return missing

    notes_with_ids = []
    notes_without_ids = []
    all_missing = []
    report = {
        "missing_ids": 0,
        "missing_notes": 0,
        "missing_note_data": [],
        "missing_id_data": []
    }
    for record in candidates:
        notes = record.get("admin", {}).get("notes", [])
        missing = _detect_missing(notes, notes_with_ids, notes_without_ids, all_missing)
        all_missing += missing

        for note in notes:
            seen = _already_seen(note, notes_with_ids, notes_without_ids)
            if not seen:
                if note.get("id") == "":
                    cnote = deepcopy(note)
                    if record.get("es_type") == "journal":
                        cnote["date"] = record.get("last_manual_update") or record.get("last_updated") or note.get("date")
                    notes_without_ids.append(cnote)
                else:
                    notes_with_ids.append(deepcopy(note))

    report["missing_ids"] = len(notes_without_ids)
    report["missing_id_data"] = notes_without_ids
    report["missing_notes"] += len(all_missing)
    report["missing_note_data"] = all_missing
    report["ordered_record_files"] = [r.get("__source_file") for r in candidates]

    result = notes_with_ids
    for n in notes_without_ids:
        n["id"] = str(uuid.uuid4())
        result.append(n)

    result.sort(key=lambda x: x.get("date", ""))
    return result, report


def main(argv=None):
    parser = argparse.ArgumentParser(description="Load .json files from subfolders into a list")
    parser.add_argument("base_dir", help="Directory containing subfolders to scan for .json files")
    parser.add_argument("--recursive", "-r", action="store_true", help="Recursively walk subfolders")
    parser.add_argument("--out_dir", "-o", help="Write the resolved notes to this output directory")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging")

    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

    try:
        load_jsons_from_dirs(args.base_dir, args.out_dir, recursive=args.recursive)
    except Exception as e:
        logging.error("Failed to load JSON files: %s", e)
        raise SystemExit(2)



if __name__ == "__main__":
    main()

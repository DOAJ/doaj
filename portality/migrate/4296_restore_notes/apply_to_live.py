# python
import os
import json
import csv
import argparse
import logging
from copy import deepcopy
from typing import List, Any
from portality.models import Journal, Application

LOG = logging.getLogger(__name__)
EARLIEST = "2026-01-14T00:00:00Z"
LATEST = "2026-01-27T00:00:00Z"

MODELS = {
    "journal": Journal,
    "application": Application
}

def load_notes_from_file(path: str) -> List[Any]:
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    # Accept either a list at top-level or a dict containing 'notes'
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("notes") or data.get("history") or []
    return []


def extract_notes_from_journal(j_obj) -> List[Any]:
    if j_obj is None:
        return []
    # If returned object is a dict
    if isinstance(j_obj, dict):
        return j_obj.get("notes") or []
    # If model with .data
    if hasattr(j_obj, "data") and isinstance(getattr(j_obj, "data"), dict):
        return j_obj.data.get("notes") or []
    # If model exposes .notes attribute
    if hasattr(j_obj, "notes"):
        return getattr(j_obj, "notes") or []
    return []


def normalize_notes(notes: List[Any]) -> set:
    """
    Convert note objects into canonical JSON strings so we can compare sets.
    """
    s = set()
    for n in notes or []:
        try:
            s.add(json.dumps(n, sort_keys=True, separators=(",", ":")))
        except Exception:
            # fallback: convert to string
            s.add(str(n))
    return s


def compute_diff(file_notes: List[Any], live_notes: List[Any]) -> dict:
    fset = normalize_notes(file_notes)
    lset = normalize_notes(live_notes)
    added = [json.loads(x) if _is_json(x) else x for x in sorted(fset - lset)]
    removed = [json.loads(x) if _is_json(x) else x for x in sorted(lset - fset)]
    return {"added": added, "removed": removed}


def _is_json(s: str) -> bool:
    try:
        json.loads(s)
        return True
    except Exception:
        return False


def process_directory(base_dir: str, out_csv: str, recursive: bool = False, record_type=None) -> int:
    rows_written = 0
    errors = 0

    # Collect candidate files
    if recursive:
        walker = ((dirpath, files) for dirpath, _, files in os.walk(base_dir))
    else:
        try:
            files = os.listdir(base_dir)
        except Exception as e:
            LOG.error("Failed to list directory %s: %s", base_dir, e)
            return 1
        walker = ((base_dir, files),)

    with open(out_csv, "w", newline="", encoding="utf-8") as csvfh:
        writer = csv.writer(csvfh)
        writer.writerow(["id", "restore_set", "notes_now", "notes_after", "diff_json"])

        for dirpath, files in walker:
            for fn in sorted(files):
                if not fn.lower().endswith(".json"):
                    continue
                if fn.startswith("_") or fn.startswith("base_"):
                    # skip files that begin with underscore or base_ (mirrors other scripts' conventions)
                    continue
                path = os.path.join(dirpath, fn)
                record_id = fn[:-5]  # strip .json
                try:
                    file_notes = load_notes_from_file(path)
                    for fn in file_notes:
                        if "flag" in fn and len(fn["flag"]) == 0:
                            del fn["flag"]
                except Exception as e:
                    LOG.exception("Failed to load JSON from %s: %s", path, e)
                    errors += 1
                    continue

                try:
                    # Pull live record from index
                    ModelClass = MODELS.get(record_type.lower()) if record_type else None
                    live_obj = ModelClass.pull(record_id)
                except Exception as e:
                    LOG.exception("Failed to pull Journal %s: %s", record_id, e)
                    errors += 1
                    continue

                live_notes = live_obj.notes
                current_notes_log = deepcopy(live_notes)
                adds = []
                removes = []
                for fn in file_notes:
                    for i, ln in enumerate(live_notes):
                        if fn.get("note") == ln.get("note"):
                            if fn.get("date") < EARLIEST or fn.get("date") > LATEST:
                                break
                            if fn.get("id") == ln.get("id"):
                                if fn.get("date") != ln.get("date") or fn.get("author") != ln.get("author"):
                                    adds.append(fn)
                                    removes.append(i)
                                else:
                                    break
                            else:
                                adds.append(fn)
                                removes.append(i)
                                break
                    else:
                        adds.append(fn)

                removes.sort(reverse=True)
                for idx in removes:
                    del live_notes[idx]
                live_notes.extend(adds)

                file_notes.sort(key=lambda x: x.get("date"))
                current_notes_log.sort(key=lambda x: x.get("date"))
                live_notes.sort(key=lambda x: x.get("date"))

                live_obj.set_notes(live_notes)
                live_obj.save()

                diff = compute_diff(live_notes, current_notes_log)

                writer.writerow([record_id,
                                 json.dumps(file_notes, indent=2),
                                 json.dumps(current_notes_log, indent=2),
                                 json.dumps(live_notes, indent=2),
                                 json.dumps(diff, ensure_ascii=False, indent=2)])
                rows_written += 1

    LOG.info("Finished. Rows written: %d, errors: %d", rows_written, errors)
    return 0 if errors == 0 else 1


def main():
    parser = argparse.ArgumentParser(description="Compare notes JSON files to live Journal records and emit diffs as CSV.")
    parser.add_argument("directory", help="Directory containing `*.json` files (filename before .json is the record ID).")
    parser.add_argument("-o", "--out", default="compare_notes.csv", help="Output CSV file (default: compare_notes.csv).")
    parser.add_argument("-t", "--type", help="Record type (journal or application)")
    parser.add_argument("-r", "--recursive", action="store_true", help="Walk directories recursively.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging.")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")

    exit_code = process_directory(args.directory, args.out, recursive=args.recursive, record_type=args.type)
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
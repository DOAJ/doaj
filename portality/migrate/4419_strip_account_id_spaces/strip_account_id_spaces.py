"""Trim leading/trailing spaces from usernames (#4419).

Usage:
    python -m portality.migrate.4419_strip_account_id_spaces.strip_account_id_spaces            # dry run, changes nothing
    python -m portality.migrate.4419_strip_account_id_spaces.strip_account_id_spaces --migrate  # do it

The username is the account's ES _id, which cannot be changed, so "bob " becomes "bob" by:
1. saving a copy of the account as "bob",
2. rewriting every record in every index that has a field exactly equal to "bob ",
3. deleting the "bob " account, only if step 2 had no failures.

If the trimmed username belongs to a different account (a clash), the account is skipped and reported.
The script can be rerun: a copy from an earlier, partial run is recognised and the job is finished.
"""

import argparse
from collections import Counter
from copy import deepcopy

from elasticsearch import helpers

from portality.core import app, es_connection as ES
from portality.models import Account


def affected_accounts():
    return sorted((a for a in Account.iterall() if a.id != a.id.strip()), key=lambda a: a.id)


def _same_account(a, b):
    # a copy we made on an earlier run, as opposed to a different person who already has the trimmed name
    return a.email == b.email and a.created_date == b.created_date


def find_references(username):
    """Every non-account record with any field exactly equal to username.
    Mapped strings have a keyword .exact; fields ES adds by itself (e.g. legacy admin.notes.author_id) get .keyword."""
    account_indices = set(ES.indices.get(index=Account.index_name()).keys())
    q = {"query": {"multi_match": {"query": username, "fields": ["*.exact", "*.keyword"], "lenient": True}}}
    for hit in helpers.scan(ES, index=app.config["ELASTIC_SEARCH_DB_PREFIX"] + "*", query=q, seq_no_primary_term=True):
        if hit["_index"] not in account_indices:
            yield hit


def _paths(obj, value, prefix=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _paths(v, value, f"{prefix}.{k}" if prefix else k)
    elif isinstance(obj, list):
        for v in obj:
            yield from _paths(v, value, prefix)
    elif obj == value:
        yield prefix


def _replace(obj, old, new):
    if isinstance(obj, dict):
        return {k: _replace(v, old, new) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_replace(v, old, new) for v in obj]
    return new if obj == old else obj


def rewrite_references(old, new):
    """Returns the number of records that could not be updated."""
    actions = []
    for hit in find_references(old):
        actions.append({
            "_op_type": "index", "_index": hit["_index"], "_id": hit["_id"],
            # only write if nobody changed the record since we read it; a rerun picks up any conflicts
            "if_seq_no": hit["_seq_no"], "if_primary_term": hit["_primary_term"],
            "_source": _replace(hit["_source"], old, new),
        })
    _, errors = helpers.bulk(ES, actions, raise_on_error=False, refresh="wait_for")
    for e in errors:
        print(f"    FAILED to update {e}")
    return len(errors)


def run(migrate=False):
    """Returns a summary dict: renamed, clashes, failed."""
    summary = {"renamed": [], "clashes": [], "failed": []}
    accounts = affected_accounts()
    print(f"{len(accounts)} account(s) with leading/trailing spaces in the username")

    for acc in accounts:
        old, new = acc.id, acc.id.strip()
        existing = Account.pull(new) if new else None
        if not new or (existing is not None and not _same_account(acc, existing)):
            print(f"CLASH  {old!r} -> {new!r}: username already in use (or blank), skipped")
            summary["clashes"].append(old)
            continue

        refs = list(find_references(old))
        print(f"RENAME {old!r} -> {new!r}, {len(refs)} linked record(s)")
        for (index, field), n in sorted(Counter((h["_index"], p) for h in refs for p in _paths(h["_source"], old)).items()):
            print(f"    {index}  {field}: {n}")
        if not migrate:
            summary["renamed"].append(old)
            continue

        if existing is None:
            data = deepcopy(acc.data)
            data["id"] = new
            Account(**data).save(blocking=True, update_last_updated=False)
        if rewrite_references(old, new):
            print(f"    {old!r} NOT deleted because some records failed; rerun to finish")
            summary["failed"].append(old)
            continue
        acc.delete()
        summary["renamed"].append(old)

    verb = "renamed" if migrate else "would be renamed"
    print(f"Done. {len(summary['renamed'])} {verb}, {len(summary['clashes'])} clash(es) skipped, "
          f"{len(summary['failed'])} failed")
    if not migrate:
        print("DRY RUN: nothing was changed. Run again with --migrate to apply.")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--migrate", action="store_true", help="apply the changes (default is a dry run)")
    run(migrate=parser.parse_args().migrate)

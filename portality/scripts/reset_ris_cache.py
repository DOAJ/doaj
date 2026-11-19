#!/usr/bin/env python3
# ~~ResetRISCache:CLI~~
"""
Reset the RIS export cache: swap the ris_export alias onto a new, empty index, then delete the old index.

The cache only saves work: RIS downloads are generated from the article on every request (and saved), articles are
re-cached by the article:ris_generator event consumer when saved, and the scheduled ris_export task fills in anything
missing. So emptying it loses nothing, and it refills over time.

Run against the read-write cluster (e.g. on the background server):
  DOAJENV=production python portality/scripts/reset_ris_cache.py [--keep-old] [--yes]

Options:
  --keep-old   Move the alias but leave the old index in place, to delete later
  --yes, -y    Skip the confirmation prompt

Afterwards, on a read-only cluster following this one via cross-cluster replication, the old follower index is left
behind (index deletes aren't replicated) and must be deleted there - with sysadmin's ansible/check_index_counts.yml
-e cleanup_stale=true, once the new index has been replicated.
"""

import argparse
import sys

from elasticsearch.exceptions import NotFoundError

from portality.core import app, es_connection
from portality.lib import dates, es_data_mapping
from portality.models import RISExport


def index_stats(indices):
    rows = es_connection.cat.indices(index=",".join(indices), format="json", bytes="b",
                                     h="index,docs.count,store.size,pri.store.size")
    return {r["index"]: r for r in rows}


def gb(b):
    return f"{int(b or 0) / 1024 ** 3:.1f} GB"


def main():
    parser = argparse.ArgumentParser(description="Reset the RIS export cache (ris_export index)",
                                     formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    parser.add_argument("--keep-old", action="store_true", help="move the alias but don't delete the old index")
    parser.add_argument("--yes", "-y", action="store_true", help="skip the confirmation prompt")
    args = parser.parse_args()

    if app.config.get("SCRIPTS_READ_ONLY_MODE", False):
        print("System is in READ-ONLY mode, enforcing read-only for this script")
        sys.exit(1)

    alias = app.config["ELASTIC_SEARCH_DB_PREFIX"] + RISExport.__type__
    print(f"Elasticsearch: {app.config['ELASTICSEARCH_HOSTS']}")

    try:
        old_indices = sorted(es_connection.indices.get_alias(name=alias).keys())
    except NotFoundError:
        if es_connection.indices.exists(index=alias):
            print(f"{alias} is a concrete index, not an alias - not touching it; sort that out by hand")
        else:
            print(f"No alias {alias} found - nothing to reset (the app creates it on startup)")
        sys.exit(1)

    for name, s in sorted(index_stats(old_indices).items()):
        print(f"Current: {name}  {s['docs.count']} docs, {gb(s['store.size'])} "
              f"({gb(s['pri.store.size'])} primary)")

    if len(old_indices) > 1:
        # move_alias only takes the alias off one index, which would leave it on two
        print(f"{alias} points at more than one index - sort that out by hand first")
        sys.exit(1)

    print(f"\nWill create a new empty {alias}-<timestamp> index, move {alias} onto it"
          + (" and keep the previous one" if args.keep_old else f", then DELETE every other {alias}-* index"))

    if not args.yes and input("Continue? (yes/no): ").lower() not in ["yes", "y"]:
        print("Cancelled.")
        return

    # The full index body (mappings + settings), so the new index gets its shards, analysis and codec settings too.
    # The rollover creates the index, moves the alias in one atomic update, then deletes older indexes by prefix.
    body = es_data_mapping.get_mappings(app)[RISExport.__type__]
    RISExport.create_and_seed_index_and_rollover_alias([], mapping=body, keep_history=1 if args.keep_old else 0)

    new_indices = sorted(es_connection.indices.get_alias(name=alias).keys())
    print(f"Moved alias {alias} -> {', '.join(new_indices)}")
    remaining = sorted(es_connection.indices.get(index=alias + "-*").keys())
    print(f"{alias}-* indexes now: {', '.join(remaining)}")


if __name__ == "__main__":
    start = dates.now()
    main()
    print(start, "-", dates.now())

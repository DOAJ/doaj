"""
Dry-run script for the 2959 multiple affiliations migration.

Scans all articles and reports which ones would be updated by the migration,
showing old and new author/affiliation details without making any real changes.

Usage:
    python -u portality/migrate/2959_multiple_affiliations/dry_run.py
"""
import logging

from portality.app import app
from portality.models import Article
from operations import migrate_affiliations

logger = logging.getLogger("2959_dry_run")


def dry_run():
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    query = {"query": {"match_all": {}}}
    total_articles = Article.count(query=query)
    logger.info("Total articles to scan: %d", total_articles)
    logger.info("=" * 80)

    updated_count = 0
    old_format_count = 0
    duplicates_merged_count = 0
    scanned_count = 0

    for source in Article.iterate(q=query, keepalive="2m", page_size=1000, wrap=False):
        scanned_count += 1
        bj = source.get("bibjson", {})
        old_authors = bj.get("author", [])

        if not old_authors:
            continue

        merged, had_old_format, had_duplicates = migrate_affiliations(source, dryrun=True)

        if had_old_format or had_duplicates:
            updated_count += 1
            if had_old_format:
                old_format_count += 1
            if had_duplicates:
                duplicates_merged_count += 1

        if scanned_count % 5000 == 0:
            logger.info("... scanned %d / %d articles, %d would be updated so far ...",
                        scanned_count, total_articles, updated_count)

    logger.info("=" * 80)
    logger.info("Dry run complete.")
    logger.info("  Total articles scanned:          %d", scanned_count)
    logger.info("  Articles that would be updated:   %d", updated_count)
    logger.info("    - With old 'affiliation' field: %d", old_format_count)
    logger.info("    - With duplicate authors merged: %d", duplicates_merged_count)
    logger.info("  Articles unchanged:               %d", scanned_count - updated_count)


if __name__ == "__main__":
    with app.app_context():
        dry_run()

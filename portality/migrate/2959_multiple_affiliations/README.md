# Issue 2959

2026-09-16

Migrate article author affiliations from the old format (single `affiliation` string per author, with
duplicate author entries for multiple affiliations) to the new format (single author entry with an
`affiliations` list).

This migration performs two operations on each article:

1. Converts any `affiliation` (string) field to the new `affiliations` (list) field.
2. Merges duplicate author entries (same name) into a single entry, combining their affiliations
   without duplicates.

## Dry Run

Run a dry run first to see how many articles would be updated, and the old/new affiliation details
for each affected article, without making any changes:

    python -u portality/migrate/2959_multiple_affiliations/dry_run.py

## Execution

Run the actual migration with

    python -u portality/upgrade.py -u portality/migrate/2959_multiple_affiliations/migrate.json

Both the dry run and the actual migration log the old and new author/affiliation details for each
updated article.

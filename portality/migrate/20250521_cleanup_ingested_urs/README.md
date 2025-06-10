# 2025-05-21; fix the URs in the wrong status due to autochecks interfering with the CSV journal ingest script

## Execution

Run the migration with

    python -u portality/upgrade.py -u portality/migrate/20250521_cleanup_ingested_urs/migrate.json
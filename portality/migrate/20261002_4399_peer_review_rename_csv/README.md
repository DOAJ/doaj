# 2026-10-02; Issue 4399 - Re-apply peer review rename after publisher CSV ingest

Publisher CSVs using the pre-4232 review process values ("Anonymous peer review", "Peer review") were ingested
before the CSV crosswalk was updated to rename them, so they were stored as "Other" free text.

This re-runs the `20260501_4232_peer_review_rename` operation, limited to records which still contain either old value.

## Execution

    python portality/upgrade.py -u portality/migrate/20261002_4399_peer_review_rename_csv/migrate.json

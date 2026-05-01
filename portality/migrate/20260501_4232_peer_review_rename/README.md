# 2026-05-01; Issue 4232 - Peer review option rename/removal

Two changes to the `bibjson.editorial.review_process` list on all journals, applications, and draft applications:

1. **Rename** `"Anonymous peer review"` → `"Single anonymous peer review"`
2. **Remove** `"Peer review"` and replace with `"Unspecified peer review"` (stored in the same list, picked up by the Other free-text field in the form)

## Execution

    python portality/upgrade.py -u portality/migrate/20260501_4232_peer_review_rename/migrate.json

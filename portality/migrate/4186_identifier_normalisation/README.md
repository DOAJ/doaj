# Issue 4186

2025-08-15

Fix identifier type for DOI to lower case, and ensure there are no extraneous identifier types present.

## Execution

Run the migration with

    python -u portality/upgrade.py -u portality/migrate/4186_identifier_normalisation/migrate.json
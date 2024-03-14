# 26 01 2024; Issue 3751 - Search bug: search results display 'Turkey' even though 'Türkiye' is used in the record

convert 'Turkey' to 'Türkiye' in Journal's index.country

## Execution

Run the migration with

    python portality/upgrade.py -u portality/migrate/3751_turkey_search/migrate.json
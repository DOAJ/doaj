Migration script to be run to remove DOAJ seal and other metadata fields.  See issues 4007 and 4015.

Run

    python portality/upgrade.py -u portality/migrate/4007_remove_the_seal/migrate.json
    python portality/upgrade.py -u portality/migrate/4007_remove_the_seal/migrate_drat_applications.json

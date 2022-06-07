https://github.com/DOAJ/doajPM/issues/3245

The script looks for applications which are rejected and if they have a `related_journal` then it tags them as update requests.

    python portality/upgrade.py -u portality/migrate/3245_ur_vs_app/migrate.json
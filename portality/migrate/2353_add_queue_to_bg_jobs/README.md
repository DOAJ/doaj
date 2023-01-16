**S.E. 2023-01-13**

Add the background job queue ID to the existing background job records in the index.
https://github.com/DOAJ/doajPM/issues/2353


Run

    python portality/upgrade.py -u portality/migrate/2353_add_queue_to_bg_jobs/migrate.json

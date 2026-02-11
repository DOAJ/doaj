# Capture New Dates in a Record's Lifespan

https://github.com/DOAJ/doajPM/issues/4080

This migration will:

* Update the index mappings for the new fields
* add "date applied" to journals from their original applications 
* set a last_withdrawn date on journals if they are withdrawn, by using the "last_updated" date 
* set a date_rejected value on applications is they are rejected, by using the "last_manual_update" date

This is run in two parts, it is essential to run them in the order defined below:

1. Update the index mappings

   ```bash
   python portality/migrate/4080_key_dates/update_mappings.py
   ```
   
2. Migrate the data

   ```bash
    python portality/upgrade.py -u portality/migrate/4080_key_dates/migrate.json
    ```
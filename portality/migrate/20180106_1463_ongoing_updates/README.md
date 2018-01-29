# 2018-01-06; Issue 1463 - Ongoing Updates

This migration covers the deployment of code to support the ongoing update
by publishers of their journal records.

This migration will carry out the following actions:

* Link all applications in the index to the journal that was derived from them
* Link all journals in the index to the applications that fed into them
* Remove any "current_journal" field on applications which are in status "accepted" or "rejected"
* Calls prep() on every suggestion, so that index.application_type is set correctly for faceting
* Exchanges any application statuses of "reapplication" to "update_request"


## Execution

First link the applications and journals together

    python portality/migrate/20180106_1463_ongoing_updates/sync_journals_applications.py

Then run the final migration, to remove unwanted data, modify statuses, and regenerate the indices:

    python portality/upgrade.py -u portality/migrate/20180106_1463_ongoing_updates/migrate.json
# Add an Application type facet

This adds an index.application_type field during prep() so that it shows "reapplication" for records which have a `current_journal` set, and "new application" otherwise.

    python portality/upgrade.py -u portality/migrate/reapplication_admin_facet/reapplication_admin_facet.json

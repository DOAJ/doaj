https://github.com/DOAJ/doajPM/issues/3245

The script looks for applications which are rejected and if they have a `related_journal` then it tags them as update requests.

    python portality/upgrade.py -u portality/migrate/3850_link_editor_groups_by_name/migrate.json
    python portality/scripts/update_mapping_for_exact.py journal index.editor_group_name
    python portality/scripts/update_mapping_for_exact.py application index.editor_group_name

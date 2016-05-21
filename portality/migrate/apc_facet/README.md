# Migrate the Has APC Facet

This changes the index.has_apc field during prep() so that it shows "No Information" for records
where there is no APC and the record is not ticked

    python portality/upgrade.py -u portality/migrate/apc_facet/apc_facet.json
    
    
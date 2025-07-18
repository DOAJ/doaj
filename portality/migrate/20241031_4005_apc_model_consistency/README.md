# Straightening out the APC model

For each journal and application, if has_apc is false, ensure any old apc data is removed

    python portality/upgrade.py -u portality/migrate/20241031_4005_apc_model_consistency/migrate.json
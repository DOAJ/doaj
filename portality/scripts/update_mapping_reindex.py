""" This script runs an esprit reindex operation, to be used if you have changed the mappings."""

import esprit
from portality.lib import es_data_mapping
from portality.core import app

if __name__ == "__main__":
    if app.config.get("SCRIPTS_READ_ONLY_MODE", False):
        print "System is in READ-ONLY mode, script cannot run"
        exit()

    new_mappings = es_data_mapping.get_mappings(app)

    old = esprit.raw.Connection("localhost", 'doaj')
    new = esprit.raw.Connection("localhost", 'doaj_notes')

    esprit.tasks.reindex(old, new, "doaj_alias", new_mappings.keys(), new_mappings, new_version="1.7.5")

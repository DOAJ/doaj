""" This script runs an esprit reindex operation, to be used if you have changed the mappings."""

import esprit
from portality.lib import es_data_mapping
from portality.core import app

if __name__ == "__main__":
    # We don't respect read-only mode (for scripts or overall) here
    # This is because this script is supposed to be run while the rest
    # of the system is in READ_ONLY_MODE and SCRIPTS_READ_ONLY_MODE
    # set to True.

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--old", help="Old / source index name.", required=True)
    parser.add_argument("-n", "--new", help="New / destination index name. Will be created if doesn't exist.", required=True)
    parser.add_argument("-a", "--alias", help="Alias currently used by old index, will be re-pointed to (or created for) new index.", required=True)
    args = parser.parse_args()

    new_mappings = es_data_mapping.get_mappings(app)

    old = esprit.raw.make_connection(None, app.config["ELASTIC_SEARCH_HOST"], None, args.old)
    new = esprit.raw.make_connection(None, app.config["ELASTIC_SEARCH_HOST"], None, args.new)

    esprit.tasks.reindex(old, new, args.alias, new_mappings.keys(), new_mappings, new_version="1.7.5")

    eq = esprit.tasks.compare_index_counts([old, new], new_mappings.keys())
    print ("all equal: ", eq)

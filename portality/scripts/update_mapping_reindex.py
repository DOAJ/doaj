""" This script runs an esprit reindex operation, to be used if you have changed the mappings."""

import esprit
from portality.lib import es_data_mapping

if __name__ == "__main__":
    if app.config.get("SCRIPTS_READ_ONLY_MODE", False):
        print "System is in READ-ONLY mode, script cannot run"
        exit()

    import argparse
    parser = argparse.ArgumentParser()

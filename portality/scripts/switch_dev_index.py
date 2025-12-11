# Switch Indexes for development
#
# THIS IS NOT FOR USE ON PRODUCTION

from portality import models
import json
from portality.core import initialise_index, app, es_connection
from portality.scripts.anon_import import do_import
from portality.util import patch_config
from portality.lib import paths

def replace_index_prefix_in_file(filepath, new_prefix):
    """
    Replace the ELASTIC_SEARCH_DB_PREFIX value in the given file with new_prefix.
    """
    import re

    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    pattern = re.compile(r'^(ELASTIC_SEARCH_DB_PREFIX\s*=\s*)["\'].*["\']\s*$')
    new_lines = []
    replaced = False

    for line in lines:
        if pattern.match(line):
            prefix_line = f'ELASTIC_SEARCH_DB_PREFIX = "{new_prefix}"\n'
            new_lines.append(prefix_line)
            replaced = True
        else:
            new_lines.append(line)

    if not replaced:
        new_lines.append(f'ELASTIC_SEARCH_DB_PREFIX = "{new_prefix}"\n')

    with open(filepath, "w", encoding="utf-8") as f:
        f.writelines(new_lines)


if __name__ == "__main__":

    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument("-c", "--cfg", help="path to local config file")
    parser.add_argument("-i", "--index", help="target index base to switch to")
    parser.add_argument("-l", "--load", help="config file for anon import, omit if no import")
    parser.add_argument('-s', '--storeimpl',
                        help="Use S3 (default) or StoreLocal as anon data source",
                        choices=['s3', 'local'],
                        default='s3',
                        required=False)

    args = parser.parse_args()

    cfg = args.cfg
    if not args.cfg:
        cfg = paths.rel2abs(__file__, "../../dev.cfg")
    print(f"Using config file: {cfg}")

    if args.index:
        replace_index_prefix_in_file(cfg, args.index)
        app.config['ELASTIC_SEARCH_DB_PREFIX'] = args.index
        initialise_index(app, es_connection)

    if args.load:
        with open(args.load, "r", encoding="utf-8") as f:
            cf = json.loads(f.read())

        if args.storeimpl == 'local':
            print("\n**\nImporting from Local storage")
            original_configs = patch_config(app, {
                'STORE_IMPL': "portality.store.StoreLocal"
            })
        else:
            print("\n**\nImporting from S3 storage")
            original_configs = patch_config(app, {
                'STORE_IMPL': "portality.store.StoreS3"
            })

        do_import(cf)
        patch_config(app, original_configs)

    print("Now restart your DOAJ development server to pick up the index change.")



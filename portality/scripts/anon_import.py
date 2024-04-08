"""
Clear out the index and retrieve new anonymised data, according to a configuration file

Configure the target index in your *.cfg override file
For now, this import script requires the same index pattern (prefix, 'types', index-per-type setting) as the exporter.

Will ignore your setting STORE_IMPL in app.cfg - defaults to s3, alternatively use local storage via [-s local]

E.g. for dev:
DOAJENV=dev python portality/scripts/anon_import.py data_import_settings/dev_basics.json

or for a test server:
DOAJENV=test python portality/scripts/anon_import.py data_import_settings/test_server.json
"""

import json, gzip, shutil, elasticsearch
from portality.core import app, es_connection, initialise_index
from portality.store import StoreFactory
from portality.dao import DomainObject
from portality import models
from doajtest.helpers import patch_config


def do_import(config):

    # filter for the types we are going to work with
    import_types = {}
    for t, s in config.get("types", {}).items():
        if s.get("import", False) is True:
            import_types[t] = s

    print("==Carrying out the following import==")
    for import_type, cfg in import_types.items():
        count = "All" if cfg.get("limit", -1) == -1 else cfg.get("limit")
        print(("{x} from {y}".format(x=count, y=import_type)))
    print("\n")

    if config.get("confirm", True):
        text = input("Continue? [y/N] ")
        if text.lower() != "y":
            exit()

    # remove all the types that we are going to import
    for import_type in list(import_types.keys()):
        try:
            if es_connection.indices.get(app.config['ELASTIC_SEARCH_DB_PREFIX'] + import_type):
                es_connection.indices.delete(app.config['ELASTIC_SEARCH_DB_PREFIX'] + import_type)
        except elasticsearch.exceptions.NotFoundError:
            pass

    # re-initialise the index (sorting out mappings, etc)
    print("==Initialising Index for Mappings==")
    initialise_index(app, es_connection)

    mainStore = StoreFactory.get("anon_data")
    tempStore = StoreFactory.tmp()
    container = app.config.get("STORE_ANON_DATA_CONTAINER")

    print("\n==Importing==")
    for import_type, cfg in import_types.items():
        count = "all" if cfg.get("limit", -1) == -1 else cfg.get("limit")
        print(("Importing {x} from {y}".format(x=count, y=import_type)))
        print(("Obtaining {x} from storage".format(x=import_type)))

        limit = cfg.get("limit", -1)
        limit = None if limit == -1 else limit

        dao = models.lookup_models_by_type(import_type, DomainObject)
        if dao:

            n = 1
            while True:
                filename = import_type + ".bulk" + "." + str(n)
                handle = mainStore.get(container, filename)
                if handle is None:
                    break
                tempStore.store(container, filename + ".gz", source_stream=handle)
                print(("Retrieved {x} from storage".format(x=filename)))
                handle.close()

                print(("Unzipping {x} in temporary store".format(x=filename)))
                compressed_file = tempStore.path(container, filename + ".gz")
                uncompressed_file = tempStore.path(container, filename, must_exist=False)
                with gzip.open(compressed_file, "rb") as f_in, open(uncompressed_file, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
                tempStore.delete_file(container, filename + ".gz")

                print(("Importing from {x}".format(x=filename)))

                imported_count = dao.bulk_load_from_file(uncompressed_file,
                                                        limit=limit, max_content_length=config.get("max_content_length", 100000000))
                tempStore.delete_file(container, filename)

                if limit is not None and imported_count != -1:
                    limit -= imported_count
                if limit is not None and limit <= 0:
                    break

                n += 1

            else:
                print(("dao class not available for the import {x}. Skipping import {x}".format(x=import_type)))

    # once we've finished importing, clean up by deleting the entire temporary container
    tempStore.delete_container(container)


if __name__ == '__main__':

    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument("config", help="Config file for import run, e.g dev_basics.json")
    parser.add_argument('-s', '--storeimpl',
                        help="Use S3 (default) or StoreLocal as anon data source",
                        choices=['s3', 'local'],
                        default='s3',
                        required=False)
    args = parser.parse_args()

    with open(args.config, "r", encoding="utf-8") as f:
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

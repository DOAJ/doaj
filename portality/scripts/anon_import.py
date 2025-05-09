"""
Clear out the index and retrieve new anonymised data, according to a configuration file

Configure the target index in your *.cfg override file
For now, this import script requires the same index pattern (prefix, 'types', index-per-type setting) as the exporter.

Will ignore your setting STORE_IMPL in app.cfg - defaults to s3, alternatively use local storage via [-s local]

E.g. for dev:
DOAJENV=dev python portality/scripts/anon_import.py data_import_settings/dev_basics.json

or for a test server:
DOAJENV=test python portality/scripts/anon_import.py data_import_settings/test_server.json

Note: max_content_length is in bytes, the default limit in ES for a bulk upload is 972.7mb (megabits) or 121.6 megabytes
"""

from __future__ import annotations

import gzip
import itertools
import json
import re
import shutil
import tempfile
import requests
from dataclasses import dataclass
from time import sleep

import portality.dao
from portality import models
from portality.scripts.createuser import create_users
from portality.core import app, es_connection
from portality.dao import DomainObject
from portality.lib import dates, es_data_mapping
from portality.store import StoreFactory
from portality.util import ipt_prefix, patch_config


@dataclass
class IndexDetail:
    index_type: str
    instance_name: str
    alias_name: str


def find_toberemoved_indexes(prefix):
    for index in portality.dao.find_indexes_by_prefix(prefix):
        if index == prefix or re.match(rf"{prefix}-\d+", index):
            yield index


def dl_test_users():
    """ Download the test user CSV from google sheets and save to tmp file for reading """

    csv_url = app.config.get('TEST_USERS_CSV_DL_PATH')
    if not csv_url:
        print("No test user CSV supplied. Skipping.")
    else:

        with tempfile.NamedTemporaryFile(delete=False) as tf:
            with requests.get(csv_url, stream=True) as r:
                for line in r.iter_lines():
                    tf.write(line + '\n'.encode())
                tf.close()

            # Supply the temp file to the create_users function
            create_users(tf.name)


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

    toberemoved_index_prefixes = [ipt_prefix(import_type) for import_type in import_types.keys()]
    toberemoved_indexes = list(itertools.chain.from_iterable(
        find_toberemoved_indexes(p) for p in toberemoved_index_prefixes
    ))
    toberemoved_index_aliases = list(portality.dao.find_index_aliases(toberemoved_index_prefixes))

    if toberemoved_indexes:
        print("==Removing the following indexes==")
        print('   {}'.format(', '.join(toberemoved_indexes)))
        print()
    if toberemoved_index_aliases:
        print("==Removing the following aliases==")
        print('   {}'.format(', '.join(alias for _, alias in toberemoved_index_aliases)))
        print()

    if config.get("confirm", True):
        text = input("Continue? [y/N] ")
        if text.lower() != "y":
            exit()

    # remove all the types that we are going to import
    for index in toberemoved_indexes:
        if es_connection.indices.exists(index):
            print("Deleting index: {}".format(index))
            es_connection.indices.delete(index, ignore=[404])

    for index, alias in toberemoved_index_aliases:
        if es_connection.indices.exists_alias(alias, index=index):
            print("Deleting alias: {} -> {}".format(index, alias))
            es_connection.indices.delete_alias(index, alias, ignore=[404])

    index_details = {}
    for import_type in import_types.keys():
        alias_name = ipt_prefix(import_type)
        index_details[import_type] = IndexDetail(
            index_type=import_type,
            instance_name=alias_name + '-{}'.format(dates.today(dates.FMT_DATE_SHORT)),
            alias_name=alias_name
        )

    # re-initialise the index (sorting out mappings, etc)
    print("==Initialising Index Mappings and alias ==")
    mappings = es_data_mapping.get_mappings(app)
    for index_detail in index_details.values():
        print("Initialising index: {}".format(index_detail.instance_name))
        es_connection.indices.create(index=index_detail.instance_name,
                                     body=mappings[index_detail.index_type],
                                     request_timeout=app.config.get("ES_SOCKET_TIMEOUT", None))

        print("Creating alias:     {:<25} -> {}".format(index_detail.instance_name, index_detail.alias_name))
        blocking_if_indices_exist(index_detail.alias_name)
        es_connection.indices.put_alias(index=index_detail.instance_name, name=index_detail.alias_name)

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

                instance_index_name = index_details[import_type].instance_name
                print("Importing from {x} to index[{index}]".format(x=filename, index=instance_index_name))

                imported_count = dao.bulk_load_from_file(uncompressed_file,
                                                         index=instance_index_name, limit=limit,
                                                         max_content_length=config.get("max_content_length", 100000000))
                tempStore.delete_file(container, filename)

                if limit is not None and imported_count != -1:
                    limit -= imported_count
                if limit is not None and limit <= 0:
                    break

                n += 1

        else:
            print(("dao class not available for the import {x}. Skipping import {x}".format(x=import_type)))

        if cfg.get("download_test_users"):
            dl_test_users()

    # once we've finished importing, clean up by deleting the entire temporary container
    tempStore.delete_container(container)


def blocking_if_indices_exist(index_name):
    for retry in range(5):
        if not es_connection.indices.exists(index_name):
            break
        print(f"Old alias exists, waiting for it to be removed, alias[{index_name}] retry[{retry}]...")
        sleep(5)


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

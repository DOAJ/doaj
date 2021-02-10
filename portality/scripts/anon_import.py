"""
Clear out the index and retrieve new anonymised data, according to a configuration file

Configure the target index in your *.cfg override file
For now, this import script requires the same index pattern (prefix, 'types', index-per-type setting) as the exporter.
"""

import esprit, json, gzip, shutil
from portality.core import app, es_connection, initialise_index
from portality.store import StoreFactory
from portality.util import ipt_prefix


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
        if es_connection.index_per_type:
            esprit.raw.delete_index(es_connection, ipt_prefix(import_type))
        else:
            esprit.raw.delete(es_connection, import_type)

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
            imported_count = esprit.tasks.bulk_load(es_connection, ipt_prefix(import_type), uncompressed_file,
                                                    limit=limit, max_content_length=config.get("max_content_length", 100000000))
            tempStore.delete_file(container, filename)

            if limit is not None and imported_count != -1:
                limit -= imported_count
            if limit is not None and limit <= 0:
                break

            n += 1

    # once we've finished importing, clean up by deleting the entire temporary container
    tempStore.delete_container(container)


if __name__ == '__main__':

    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument("config", help="Config file for import run")
    args = parser.parse_args()

    with open(args.config, "r", encoding="utf-8") as f:
        config = json.loads(f.read())

    do_import(config)

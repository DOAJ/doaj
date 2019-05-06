import esprit, codecs, json, gzip, shutil
from portality.core import app, initialise_index
from portality.store import StoreFactory
from botocore.exceptions import ClientError


def do_import(config):
    host = app.config["ELASTIC_SEARCH_HOST"]
    index = app.config["ELASTIC_SEARCH_DB"]
    if config.get("elastic_search_host") is not None:
        host = config.get("elastic_search_host")
        app.config["ELASTIC_SEARCH_HOST"] = host
    if config.get("elastic_search_db") is not None:
        index = config.get("elastic_search_db")
        app.config["ELASTIC_SEARCH_DB"] = index

    print("\n")
    print("Using host {x} and index {y}\n".format(x=host, y=index))
    conn = esprit.raw.make_connection(None, host, None, index)

    # filter for the types we are going to work with
    import_types = {}
    for t, s in config.get("types", {}).iteritems():
        if s.get("import", False) is True:
            import_types[t] = s

    print("==Carrying out the following import==")
    for import_type, cfg in import_types.iteritems():
        count = "All" if cfg.get("limit", -1) == -1 else cfg.get("limit")
        print("{x} from {y}".format(x=count, y=import_type))
    print("\n")

    if config.get("confirm", True):
        text = raw_input("Continue? [y/N] ")
        if text.lower() != "y":
            exit()

    # remove all the types that we are going to import
    for import_type in import_types.keys():
        esprit.raw.delete(conn, import_type)

    # re-initialise the index (sorting out mappings, etc)
    print("==Initialising Index for Mappings==")
    initialise_index(app)

    mainStore = StoreFactory.get("anon_data")
    tempStore = StoreFactory.tmp()
    container = app.config.get("STORE_ANON_DATA_CONTAINER")

    print("\n==Importing==")
    for import_type, cfg in import_types.iteritems():
        count = "all" if cfg.get("limit", -1) == -1 else cfg.get("limit")
        print("Importing {x} from {y}".format(x=count, y=import_type))
        print("Obtaining {x} from storage".format(x=import_type))

        limit = cfg.get("limit", -1)
        limit = None if limit == -1 else limit

        n = 1
        while True:
            filename = import_type + ".bulk" + "." + str(n)
            handle = mainStore.get(container, filename)
            if handle is None:
                break
            tempStore.store(container, filename + ".gz", source_stream=handle)
            print("Retrieved {x} from storage".format(x=filename))
            handle.close()

            print("Unzipping {x} in temporary store".format(x=filename))
            compressed_file = tempStore.path(container, filename + ".gz")
            uncompressed_file = tempStore.path(container, filename, must_exist=False)
            with gzip.open(compressed_file, "rb") as f_in, open(uncompressed_file, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
            tempStore.delete_file(container, filename + ".gz")

            print("Importing from {x}".format(x=filename))
            imported_count = esprit.tasks.bulk_load(conn, import_type, uncompressed_file,
                                                    limit=limit, max_content_length=config.get("max_content_length", 100000000))
            tempStore.delete_file(container, filename)

            if limit is not None and imported_count != -1:
                limit -= imported_count
            if limit is not None and limit <= 0:
                break

            n += 1

    tempStore.delete_file(container)

if __name__ == '__main__':

    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument("config", help="Config file for import run")
    args = parser.parse_args()

    with codecs.open(args.config, "rb", "utf-8") as f:
        config = json.loads(f.read())

    do_import(config)

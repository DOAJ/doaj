import esprit, os, codecs, json
from portality.core import app, initialise_index


def do_import(config):
    host = app.config["ELASTIC_SEARCH_HOST"]
    index = app.config["ELASTIC_SEARCH_DB"]
    if config.get("elastic_search_host") is not None:
        host = config.get("elastic_search_host")
        app.config["ELASTIC_SEARCH_HOST"] = host
    if config.get("elastic_search_db") is not None:
        index = config.get("elastic_search_db")
        app.config["ELASTIC_SEARCH_DB"] = index

    source = config.get("source")
    if source is None:
        raise Exception("Must provide a source directory for the import files")

    print("Using host {x} and index {y}".format(x=host, y=index))
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
        text = raw_input("Continue? [y/n]")
        if text.lower() != "Y":
            exit()

    # remove all the types that we are going to import
    for import_type in import_types.keys():
        esprit.raw.delete(conn, import_type)

    # re-initialise the index (sorting out mappings, etc)
    print("==Initialising Index for Mappings==")
    initialise_index(app)

    print("\n==Importing==")
    for import_type, cfg in import_types.iteritems():
        count = "all" if cfg.get("limit", -1) == -1 else cfg.get("limit")
        print("Importing {x} from {y}".format(x=count, y=import_type))

        data_file = os.path.join(source, import_type + ".bulk")
        limit = cfg.get("limit", -1)
        limit = None if limit == -1 else limit
        esprit.tasks.bulk_load(conn, import_type, data_file, limit=limit, max_content_length=config.get("max_content_length", 100000000))


if __name__ == '__main__':

    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument("config", help="Config file for import run")
    args = parser.parse_args()

    with codecs.open(args.config, "rb", "utf-8") as f:
        config = json.loads(f.read())

    do_import(config)

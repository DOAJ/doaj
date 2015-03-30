import json, os, esprit
from portality.core import app
from portality import models

MODELS = {
    "journal" : models.Journal,
    "article" : models.Article
}

class UpgradeTask(object):

    def upgrade_article(self, article):
        pass

def do_upgrade(definition):
    # get the source and target es definitions
    source = definition.get("source")
    target = definition.get("target")

    if source is None:
        source = {
            "host" : app.config.get("ELASTIC_SEARCH_HOST"),
            "index" : app.config.get("ELASTIC_SEARCH_DB")
        }

    if target is None:
        target = {
            "host" : app.config.get("ELASTIC_SEARCH_HOST"),
            "index" : app.config.get("ELASTIC_SEARCH_DB"),
            "mappings" : False
        }

    sconn = esprit.raw.Connection(source.get("host"), source.get("index"))
    tconn = esprit.raw.Connection(target.get("host"), target.get("index"))

    # get the defined batch size
    batch_size = definition.get("batch", 1000)

    for tdef in definition.get("types", []):
        print "Upgrading", tdef.get("type")
        batch = []
        for result in esprit.tasks.scroll(sconn, tdef.get("type"), keepalive=tdef.get("keepalive", "1m")):
            # instantiate an object with the data
            m = MODELS.get(tdef.get("type"))
            obj = m(**result)

            # FIXME: do something with explicit upgrade tasks

            # run the prep routine for the record
            try:
                obj.prep()
            except AttributeError:
                pass

            # add the data to the batch
            batch.append(obj.data)

            # When we have enough, do some writing
            if len(batch) >= batch_size:
                print "writing ", len(batch)
                esprit.raw.bulk(tconn, tdef.get("type"), batch)
                batch = []

        # Write the last part-batch to index
        if len(batch) > 0:
            print "writing ", len(batch)
            esprit.raw.bulk(tconn, tdef.get("type"), batch)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--upgrade", help="path to upgrade definition")
    args = parser.parse_args()

    if not args.upgrade:
        print "Please specify an upgrade package with the -u option"
        exit()

    if not (os.path.exists(args.upgrade) and os.path.isfile(args.upgrade)):
        print args.upgrade, "does not exist or is not a file"
        exit()

    with open(args.upgrade) as f:
        try:
            definition = json.loads(f.read())
        except:
            print args.upgrade, "does not parse as JSON"
            exit()

        do_upgrade(definition)

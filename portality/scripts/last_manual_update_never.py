from portality import models
from portality.core import app
from portality.clcsv import UnicodeWriter
import esprit
import codecs


LAST_MANUAL_UPDATE_NEVER = {
     "query": {
        "filtered": {
        	"query": { "term": {"last_manual_update": "1970-01-01T00:00:00Z"}},
            "filter": {
            	"bool": {
	                "must": { "term": {"in_doaj": "true"}}
	            }
            }
        }
    },
    "sort": [{
        "created_date": "asc"
    }]
}

if __name__ == "__main__":

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--out", help="output file path")
    args = parser.parse_args()

    if not args.out:
        print "Please specify an output file path with the -o option"
        parser.print_help()
        exit()

    conn = esprit.raw.make_connection(None, app.config["ELASTIC_SEARCH_HOST"], None, app.config["ELASTIC_SEARCH_DB"])

    with codecs.open(args.out, "wb", "utf-8") as f:
        writer = UnicodeWriter(f)
        writer.writerow(["ID", "Journal Name", "E-ISSN", "P-ISSN", "Created Date"])

        for j in esprit.tasks.scroll(conn, models.Journal.__type__, q=LAST_MANUAL_UPDATE_NEVER, limit=800, keepalive='5m'):
            journal = models.Journal(_source=j)
            bibjson = journal.bibjson()
            issns = bibjson.issns()

            writer.writerow([journal.id, bibjson.title, bibjson.get_one_identifier(bibjson.E_ISSN), bibjson.get_one_identifier(bibjson.P_ISSN), journal.created_date])
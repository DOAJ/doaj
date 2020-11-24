from portality import models
from portality.core import es_connection
from portality.util import ipt_prefix
import esprit
import csv


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
        print("Please specify an output file path with the -o option")
        parser.print_help()
        exit()

    conn = es_connection

    with open(args.out, "w", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID",
                         "Journal Name",
                         "Journal URL",
                         "E-ISSN",
                         "P-ISSN",
                         "Created Date",
                         "Owner",
                         "Owner's email address",
                         "Country",
                         "Publisher"])

        for j in esprit.tasks.scroll(conn, ipt_prefix(models.Journal.__type__), q=LAST_MANUAL_UPDATE_NEVER, limit=800, keepalive='5m'):
            journal = models.Journal(_source=j)
            bibjson = journal.bibjson()
            index = j["index"]
            owner = journal.owner
            account = models.Account.pull(owner)

            writer.writerow([journal.id,
                             bibjson.title,
                             bibjson.get_single_url(urltype="homepage"),
                             bibjson.get_one_identifier(bibjson.E_ISSN),
                             bibjson.get_one_identifier(bibjson.P_ISSN),
                             journal.created_date,
                             owner,
                             account.email,
                             index["country"],
                             bibjson.publisher
                             ])

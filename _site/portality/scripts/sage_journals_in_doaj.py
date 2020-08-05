from portality import models
from portality.core import app
import esprit
import csv


SAGE_JOURNALS_IN_DOAJ = {
     "query":{
    "filtered":{
        "filter":{
            "bool":{
                "must":[
                    {"term":{"index.publisher.exact":"SAGE Publishing"}},
                    {"term" : {"admin.in_doaj" : True}}
                 ]
             }
         },
         "query":{
            "match_all":{}
        }
    }
}
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

    conn = esprit.raw.make_connection(None, app.config["ELASTIC_SEARCH_HOST"], None, app.config["ELASTIC_SEARCH_DB"])

    with open(args.out, "w", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID",
                         "Title"])

        for j in esprit.tasks.scroll(conn, models.Journal.__type__, q=SAGE_JOURNALS_IN_DOAJ, limit=800, keepalive='5m'):
            journal = models.Journal(_source=j)
            bibjson = journal.bibjson()

            writer.writerow([journal.id,
                             bibjson.title
                             ])

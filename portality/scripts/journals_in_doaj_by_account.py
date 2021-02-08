from portality import models
from portality.core import app
from portality.core import es_connection
import esprit
import csv
import json
from portality.util import ipt_prefix

class JournalQuery(object):
    def __init__(self, owner):
        self.owner = owner

    def query(self):
        return {
            "query":{
                "filtered":{
                    "filter":{
                        "bool":{
                            "must":[
                                {"term":{"admin.owner.exact": self.owner}},
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
    parser.add_argument("-i", "--input", help="input account list")
    parser.add_argument("-o", "--out", help="output file path")
    args = parser.parse_args()

    if not args.out:
        print("Please specify an output file path with the -o option")
        parser.print_help()
        exit()

    if not args.input:
        print("Please specify an input file path with the -i option")
        parser.print_help()
        exit()

    # conn = esprit.raw.make_connection(None, app.config["ELASTIC_SEARCH_HOST"], None, app.config["ELASTIC_SEARCH_DB"])
    conn = es_connection

    with open(args.out, "w", encoding="utf-8") as f, open(args.input, "r") as g:
        reader = csv.reader(g)

        writer = csv.writer(f)
        writer.writerow(["Name", "Account", "ID", "Title"])

        for row in reader:
            query = JournalQuery(row[1])
            print(json.dumps(query.query()))
            count = 0
            for j in esprit.tasks.scroll(conn, ipt_prefix(models.Journal.__type__), q=query.query(), limit=800, keepalive='5m'):
                journal = models.Journal(_source=j)
                bibjson = journal.bibjson()

                writer.writerow([row[0], row[1], journal.id, bibjson.title])
                count += 1
            print(count)
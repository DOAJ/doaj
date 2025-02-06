from portality.models import Journal
import csv
import json


class JournalQuery(object):
    def __init__(self, owner):
        self.owner = owner

    def query(self):
        return {
            "track_total_hits": True,
            "query": {
                "bool": {
                    "must": [
                        {"term": {"admin.owner.exact": self.owner}},
                        {"term": {"admin.in_doaj": True}}
                     ]
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

    with open(args.out, "w", encoding="utf-8") as f, open(args.input, "r") as g:
        reader = csv.reader(g)

        writer = csv.writer(f)
        writer.writerow(["Name", "Account", "ID", "Title"])

        for row in reader:
            query = JournalQuery(row[1])
            print(json.dumps(query.query()))
            count = 0
            for journal in Journal.scroll(q=query.query(), page_size=100, keepalive='5m', limit=800):
                bibjson = journal.bibjson()

                writer.writerow([row[0], row[1], journal.id, bibjson.title])
                count += 1
            print(count)

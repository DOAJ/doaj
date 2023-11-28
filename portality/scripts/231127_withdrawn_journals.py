from portality.models import Journal
import csv


NOT_IN_DOAJ = {
    "query" : {
        "bool" : {
            "must" : [
                {"term" : {"admin.in_doaj" : False}}
            ]
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

    with open(args.out, "w", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID",
                         "Journal Name",
                         "Journal URL",
                         "E-ISSN",
                         "P-ISSN"
                         ])

        for journal in Journal.iterate(q=NOT_IN_DOAJ, keepalive='5m', wrap=True):
            bibjson = journal.bibjson()

            writer.writerow([journal.id,
                             bibjson.title,
                             bibjson.get_single_url(urltype="homepage"),
                             bibjson.get_one_identifier(bibjson.E_ISSN),
                             bibjson.get_one_identifier(bibjson.P_ISSN),
                             ])





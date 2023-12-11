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

IN_DOAJ = {
    "query" : {
        "bool" : {
            "must" : [
                {"term" : {"admin.in_doaj" : True}}
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

        in_doaj_issns = set()
        for journal in Journal.iterate(q=IN_DOAJ, keepalive='5m', wrap=True):
            bibjson = journal.bibjson()
            in_doaj_issns.add(bibjson.get_one_identifier(bibjson.E_ISSN))
            in_doaj_issns.add(bibjson.get_one_identifier(bibjson.P_ISSN))


        for journal in Journal.iterate(q=NOT_IN_DOAJ, keepalive='5m', wrap=True):
            bibjson = journal.bibjson()
            eissn = bibjson.get_one_identifier(bibjson.E_ISSN)
            pissn = bibjson.get_one_identifier(bibjson.P_ISSN)
            if (eissn not in in_doaj_issns and pissn not in in_doaj_issns):
                writer.writerow([journal.id,
                                 bibjson.title,
                                 bibjson.get_single_url(urltype="homepage"),
                                 eissn,
                                 pissn,
                                 ])





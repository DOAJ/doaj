import codecs, csv

from portality import constants
from portality import models, datasets


def do_report(out):
    with codecs.open(out, "wb", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Title", "ISSN(s)", "Country Code", "Country", "Status", "Date Applied", "Last Manual Update", "Last Update", "Notes"])
        gen = models.Suggestion.list_by_status(constants.APPLICATION_STATUS_REJECTED)
        for s in gen:
            bj = s.bibjson()
            title = bj.title
            issns = bj.issns()
            cc = bj.country
            applied = s.created_date
            last_manual = s.last_manual_update
            last_update = s.last_updated
            notes = s.notes
            status = s.application_status

            if title is None:
                title = ""
            if issns is None:
                issns = []
            if cc is None:
                cc = ""
            if applied is None:
                applied = ""
            if last_manual is None:
                last_manual = "never"
            if last_update is None:
                last_update = "never"
            if notes is None:
                notes = []
            if status is None:
                status = "unknown"

            issns = ", ".join(issns)
            notes = "\n\n".join(["[" + n.get("date") + "] " + n.get("note") for n in notes])

            country = datasets.get_country_name(cc)

            writer.writerow([title, issns, cc, country, status, applied, last_manual, last_update, notes])

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--out", help="output file path")
    args = parser.parse_args()

    if not args.out:
        print("Please specify an output file path with -o")
        exit()

    do_report(args.out)
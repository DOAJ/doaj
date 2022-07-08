import csv
import esprit
from portality.core import es_connection, app
from portality.util import ipt_prefix
from portality import models, constants

def non_rejected_urs_of_journals_not_in_doaj(csvwriter=None):
    """ Scroll through all applications, return unrejected update requests of journals that are no longer in doaj
    """
    urs = []
    for app in models.Application.iterate():
        if app.application_type != constants.APPLICATION_TYPE_UPDATE_REQUEST:
            continue

        if app.application_status != constants.APPLICATION_STATUS_REJECTED:
            if app.current_journal:
                j = models.Journal.pull(app.current_journal)
                if j.is_in_doaj():
                    urs.append(app.id)

    return urs

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
        writer.writerow(["update request id"])

        for ur in non_rejected_urs_of_journals_not_in_doaj():
            print(ur)
            writer.writerow([
                ur
            ])


import csv
from portality import models, constants


def non_rejected_urs_of_journals_not_in_doaj(include_missing: bool, csv_writer: csv.writer):
    """ Scroll through all applications, return unrejected update requests of journals that are no longer in doaj """
    urs = []
    csv_writer.writerow(["Application ID", "Reason"])
    for app in models.Application.iterate():
        if app.application_type != constants.APPLICATION_TYPE_UPDATE_REQUEST:
            continue

        if app.application_status != constants.APPLICATION_STATUS_REJECTED:
            if app.current_journal:
                j = models.Journal.pull(app.current_journal)

                if j is None:
                    writer.writerow([app.id, f"Journal {app.current_journal} could not be found"])
                elif not j.is_in_doaj():
                    writer.writerow([app.id, f"Journal {app.current_journal} not in DOAJ"])
            else:
                if include_missing:
                    writer.writerow([app.id, "Application's current_journal is missing"])

    return urs


if __name__ == "__main__":

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--out", help="output file path", default=f'{__file__}_out.csv')
    parser.add_argument("-f", "--full", help="Report on mising current_journal fields", action='store_true')
    args = parser.parse_args()

    with open(args.out, "w", encoding="utf-8") as f:
        writer = csv.writer(f)
        non_rejected_urs_of_journals_not_in_doaj(args.full, writer)

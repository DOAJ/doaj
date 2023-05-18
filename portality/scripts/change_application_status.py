from portality.core import app
import csv

from portality.lib import dates
from portality.models import Suggestion
from portality.forms.application_forms import ApplicationFormFactory, application_statuses


def change_status(ids, new_status):
    fc = ApplicationFormFactory.context("admin")
    statuses = [x[0] for x in application_statuses(None, fc) if x[0] != ""]
    if new_status not in statuses:
        raise Exception("Must use an allowed status: " + ", ".join(statuses))

    for id in ids:
        a = Suggestion.pull(id)
        a.set_application_status(new_status)
        a.save()


if __name__ == "__main__":
    print('Starting {0}.'.format(dates.now()))

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--csv", help="csv containing ids to change")
    parser.add_argument("-s", "--status", help="new status to set")
    args = parser.parse_args()

    if app.config.get("SCRIPTS_READ_ONLY_MODE", False):
        print("System is in READ-ONLY mode, enforcing read-only for this script")
        args.write = False

    if not args.csv or not args.status:
        print("You must provide both the -c and -s options. Exiting.")
        exit(1)

    with open(args.csv, "r") as f:
        reader = csv.reader(f)
        ids = [row[0] for row in reader]
        change_status(ids, args.status)

    print('Finished {0}.'.format(dates.now()))
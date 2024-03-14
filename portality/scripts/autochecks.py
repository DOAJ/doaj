from portality.bll import DOAJ
from portality import models
from portality.lib import dates
import csv


if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("-i", "--id", help="ID of application or journal on which to run autocheck")
    parser.add_argument("-a", "--applications", help="CSV of application IDs on which to run autochecks")
    parser.add_argument("-j", "--journals", help="CSV of journal IDs on which to run autochecks")
    parser.add_argument("-A", "--all_applications", help="Run autochecks on all applications", action="store_true")
    parser.add_argument("-J", "--all_journals", help="Run autochecks on all journals", action="store_true")

    args = parser.parse_args()
    if args.id is None and args.applications is None and args.journals is None and args.all_applications is None and args.all_journals is None:
        print("You must specify an application id with the -i argument, or a list of ids in a csv with the -a/A or -j/J arguments for applications and journals respectively")
        exit(1)

    if args.id is not None and (args.applications is not None or args.all_applications is not None or args.journals is not None or args.all_journals is not None):
        print("You cannot specify both -i and -a/A or -j/J")
        exit(1)

    if args.applications is not None and args.all_applications is not None:
        print("You cannot specify both -a and -A")
        exit(1)

    if args.journals is not None and args.all_journals is not None:
        print("You cannot specify both -j and -J")
        exit(1)

    anno_svc = DOAJ.autochecksService()

    logger = lambda x: print(dates.now_str_with_microseconds() + " " + x)

    if args.id:
        application = models.Application.pull(args.id)
        if application is not None:
            print("\nAnnotating application {x}".format(x=application.id))
            anno_svc.autocheck_application(application, logger=logger)
            exit(1)

        journal = models.Journal.pull(args.id)
        if journal is not None:
            print("\nAnnotating journal {x}".format(x=journal.id))
            anno_svc.autocheck_journal(journal, logger=logger)
            exit(1)

        print("ID did not resolve to an application or journal")
        exit(1)

    if args.all_applications:
        print("Autochecking all applications")
        anno_svc.autocheck_applications(logger=logger)

    if args.all_journals:
        print("Autochecking all journals")
        anno_svc.autocheck_journals(logger=logger)

    if args.applications:
        print("Autochecking applications from {x}".format(x=args.applications))
        with open(args.applications, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                application = None
                id = row[0].strip()
                if len(id) == 9:
                    applications = models.Application.find_by_issn(id)
                    if len(applications) > 0:
                        application = applications[0]
                else:
                    application = models.Application.pull(id)

                if application is None:
                    print("Application ID {x} did not resolve to an application".format(x=id))
                    continue
                print("\nAnnotating application {x}".format(x=application.id))
                anno_svc.autocheck_application(application, logger=lambda x: print(x))

    if args.journals:
        print("Autochecking journals from {x}".format(x=args.journals))
        with open(args.journals, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                journal = None
                id = row[0].strip()
                if len(id) == 9:
                    journals = models.Journal.find_by_issn(id)
                    if len(journals) > 0:
                        journal = journals[0]
                else:
                    journal = models.Journal.pull(id)

                if journal is None:
                    print("Journal ID {x} did not resolve to a journal".format(x=id))
                    continue
                print("\nAnnotating journal {x}".format(x=journal.id))
                anno_svc.autocheck_journal(journal, logger=lambda x: print(x))
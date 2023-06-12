from portality.bll import DOAJ
from portality import models
import csv


if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("-i", "--id", help="ID of application or journal on which to run annotations")
    parser.add_argument("-a", "--applications", help="CSV of application IDs on which to run annotations")
    parser.add_argument("-j", "--journals", help="CSV of journal IDs on which to run annotations")

    args = parser.parse_args()
    if args.applications is None and args.journals is None:
        print("You must specify an application id with the -i argument, or a list of ids in a csv with the -a or -j arguments for applications and journals respectively")
        exit(1)

    anno_svc = DOAJ.annotationsService()

    if args.id:
        application = models.Application.pull(args.id)
        if application is not None:
            print("\nAnnotating application {x}".format(x=application.id))
            anno_svc.annotate_application(application, logger=lambda x: print(x))
            exit(1)

        journal = models.Journal.pull(args.id)
        if journal is not None:
            print("\nAnnotating journal {x}".format(x=journal.id))
            anno_svc.annotate_journal(journal, logger=lambda x: print(x))
            exit(1)

        print("ID did not resolve to an application or journal")
        exit(1)

    if args.applications:
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
                anno_svc.annotate_application(application, logger=lambda x: print(x))

    if args.journals:
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
                anno_svc.annotate_journal(journal, logger=lambda x: print(x))
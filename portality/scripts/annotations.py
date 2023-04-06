from portality.bll import DOAJ
from portality import models

if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("-a", "--application", help="ID of application on which to run annotations")
    parser.add_argument("-j", "--journal", help="ID of journal on which to run annotations")

    args = parser.parse_args()
    if args.application is None and args.journal is None:
        print("You must specify an application id with the -a argument, or a journal with the -j argument")
        exit(1)

    anno_svc = DOAJ.annotationsService()

    if args.application:
        application = models.Application.pull(args.application)
        if application is None:
            print("Application ID did not resolve to an application")
            exit(1)
        print("\nAnnotating application {x}".format(x=application.id))
        anno_svc.annotate_application(application, logger=lambda x: print(x))

    if args.journal:
        journal = models.Journal.pull(args.journal)
        if journal is None:
            print("Journal ID did not resolve to a journal record")
            exit(1)
        print("\nAnnotating journal {x}".format(x=journal.id))
        anno_svc.annotate_journal(journal, logger=lambda x: print(x))
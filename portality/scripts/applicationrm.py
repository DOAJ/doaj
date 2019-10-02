from portality import models
from portality.core import app

if __name__ == "__main__":

    if app.config.get("SCRIPTS_READ_ONLY_MODE", False):
        print ("System is in READ-ONLY mode, script cannot run")
        exit()

    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument("-e", "--email", help="email of the suggester whose applications to remove")
    parser.add_argument("-s", "--status", help="comma separated list of statuses to remove; if none provided all applications will be removed")

    args = parser.parse_args()

    if not args.email:
        print ("Please specify an username with the -e option")
        exit()

    statuses = []
    if args.status:
        statuses = [s.strip() for s in args.status.split(",")]

    query = {}
    models.Suggestion.delete_selected(email=args.email, statuses=statuses)


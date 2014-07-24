from portality import models

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument("-e", "--email", help="email of the suggester whose applications to remove")
    parser.add_argument("-s", "--status", help="comma separated list of statuses to remove; if none provided all applications will be removed")

    args = parser.parse_args()

    if not args.email:
        print "Please specify an username with the -e option"
        exit()

    statuses = []
    if args.status:
        statuses = [s.strip() for s in args.status.split(",")]

    query = {}
    models.Suggestion.delete_selected(email=args.email, statuses=statuses)


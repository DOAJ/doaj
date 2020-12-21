""" Copy contact details from old applications in old index to a note in new applications in new index.
https://github.com/DOAJ/doajPM/issues/2634

    Query the current live index for applications which don't have owners and in statuses:
        Pending
        In progress
        Completed
        Ready
        On hold
    Get the Suggester and the Journal Contact details from the equivalent record on the old index
    Make a note clearly labelling the Suggester and Journal Contact
    Attach that note to the live record for each one

    To the above I've also added the account owner ID from the old suggestion record in the case that it can't be
    found in the current index.

usage: python 2634_copy_across_contact_details.py -o run.csv [-w]
"""

import csv
import esprit
from portality.core import es_connection, app
from portality import models

IN_STATUSES = {
    "query": {
        "filtered": {
            "filter": {
                "bool": {
                    "should": [
                        {
                            "term": {"admin.application_status.exact":"pending"}
                        },
                        {
                            "term": {"admin.application_status.exact":"in progress"}
                        },
                        {
                            "term": {"admin.application_status.exact":"completed"}
                        },
                        {
                            "term": {"admin.application_status.exact":"ready"}
                        },
                        {
                            "term": {"admin.application_status.exact": "on hold"}
                        }
                    ]
                }
            },
            "query": {
                "match_all": {}
            }
        }
    }
}


def old_application_sources(conn):
    for sugg in esprit.tasks.scroll(conn, 'suggestion', q=IN_STATUSES, page_size=100, keepalive='1m'):

        # Only include this suggestion if we can't find the owner in the current index
        if models.Account.pull(sugg.get('admin', {}).get('owner', '')) is None:
            owner = sugg.get('admin', {}).get('owner', '')
            suggester = sugg.get('suggestion', {}).get('suggester', {})
            contact = sugg.get('admin', {}).get('contact', [])
            yield sugg['id'], owner, suggester, contact


def add_note_to_new_application(_id, owner, suggester, contact):
    """ Pull and add note to the current version of an application """
    application = models.Application.pull(_id)
    if application is not None:
        note = 'Details from old index added by script doajPM issue 2634 - \n'
        if owner:
            note += '\nOwner ID (not found in current index): {0}\n'.format(owner)
        if suggester:
            note += '\nSuggester\n'
            if suggester.get('name'):
                note += suggester['name'] + '\n'
            if suggester.get('email'):
                note += suggester['email'] + '\n'
        if contact:
            note += '\nContact\n'
            for con in contact:
                if con.get('name'):
                    note += con['name'] + '\n'
                if con.get('email'):
                    note += con['email'] + '\n'

        if owner == suggester == contact == '':
            note += 'No contact details found in old index'

        application.add_note(note)
        application.save()


if __name__ == "__main__":
    if app.config.get("SCRIPTS_READ_ONLY_MODE", False):
        print("System is in READ-ONLY mode, script cannot run")
        exit()

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--out", help="output file path", required=True)
    parser.add_argument("-w", "--write", help="write changes to index", action='store_true')
    args = parser.parse_args()

    if not args.out:
        print("Please specify an output file path with the -o option")
        parser.print_help()
        exit()

    if not args.write:
        print("Write argument [-w] not specified - notes will not be written to the new applications.")

    sconn = esprit.raw.Connection(app.config.get("ELASTIC_SEARCH_HOST"), app.config.get("ELASTIC_SEARCH_DB"))
    tconn = es_connection
    prefix = app.config.get("ELASTIC_SEARCH_DB_PREFIX")

    with open(args.out, "w", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Owner", "Journal Contact", "Suggester"])

        for _id, o, s, c in old_application_sources(sconn):
            if args.write:
                add_note_to_new_application(_id, o, s, c)

            writer.writerow([_id, o, s, c])

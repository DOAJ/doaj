"""
Delete a specified field from all records of a certain type in the index.
FIXME: Doesn't work on fields in lists. e.g. for https://github.com/DOAJ/doajPM/issues/1667 to remove author emails from articles
"""

import esprit
from portality.core import app
from portality.lib import dataobj
from datetime import datetime


def scrub_field(connection, o_type, o_field, batch_size=500):

    batch = []

    for o in esprit.tasks.scroll(connection, o_type):
        # Access the data using the DataObj class
        o_obj = dataobj.DataObj(raw=o)
        o_obj._delete(o_field)

        batch.append(o_obj.data)

        if len(batch) >= batch_size:
            esprit.raw.bulk(connection, batch, idkey='id', type_=o_type)
            batch = []

    # Finish saving the final batch
    esprit.raw.bulk(connection, batch, idkey='id', type_=o_type)


if __name__ == "__main__":
    start = datetime.now()

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-t",
                        "--type",
                        help="The type from which the field is to be removed",
                        required=True)
    parser.add_argument('-f',
                        '--field',
                        help='The field to remove from all documents of the specified type, in dot notation e.g. "admin.unwanted_field"',
                        required=True)
    args = parser.parse_args()

    if app.config.get("SCRIPTS_READ_ONLY_MODE", False):
        print("System is in READ-ONLY mode, script cannot run")
        exit(1)

    # Connection to the ES index, rely on esprit sorting out the port from the host
    conn = esprit.raw.make_connection(None, app.config["ELASTIC_SEARCH_HOST"], None, app.config["ELASTIC_SEARCH_DB"])

    # Make sure the user is super serious about doing this.
    resp = raw_input("\nAre you sure? This script can be VERY DESTRUCTIVE!\n"
                     "Confirm delete of field {0} in type {1} y/N: ".format(args.field, args.type))
    if resp.lower() == 'y':
        # Run the function to remove the field
        print("Okay, here we go...")
        scrub_field(conn, args.type, args.field)
    else:
        print("Better safe than sorry, exiting.")

    end = datetime.now()
    print(str(start) + "-" + str(end))

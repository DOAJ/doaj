"""
FIXME: This script has been around for a few years, it'll need a bit of work to reinstate if needed again
* model lookup by type

Delete a specified field from all records of a certain type in the index.
FIXME: Doesn't work on fields in lists. e.g. for https://github.com/DOAJ/doajPM/issues/1667 to remove author emails from articles
"""

from portality.core import app
from datetime import datetime


def scrub_field(o_type, o_field, batch_size=500):

    batch = []

    model_class = MODELS.get(o_type.get("type"))

    for o_obj in model_class.scroll():
        o_obj._delete(o_field)

        batch.append(o_obj.data)

        if len(batch) >= batch_size:
            o_obj.bulk(batch, idkey='id')
            batch = []

    # Finish saving the final batch
    o_obj.bulk(batch, idkey='id')


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

    # Make sure the user is super serious about doing this.
    resp = input("\nAre you sure? This script can be VERY DESTRUCTIVE!\n"
                     "Confirm delete of field {0} in type {1} y/N: ".format(args.field, args.type))
    if resp.lower() == 'y':
        # Run the function to remove the field
        print("Okay, here we go...")
        scrub_field(args.type, args.field)
    else:
        print("Better safe than sorry, exiting.")

    end = datetime.now()
    print((str(start) + "-" + str(end)))

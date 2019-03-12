"""
This script allows us to generate the public data dumps for the system.  It provides a number of
command line options, and it is IMPORTANT to note that in production it MUST only be run with the
following arguments:


     public_data_dump.py all -p

If you run this in production with either `journal` or `article` as the first positional argument,
then any existing link to the other data type will be no longer available.

If you run this with the `-c` option, there is a chance that in the event of an error the live
data will be deleted, and not replaced with new data.  Better to prune with `-p` after the
new data has been generated instead.
"""

from portality.core import app
from portality.tasks import public_data_dump
from portality.background import BackgroundApi

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("type", choices=['article','journal', 'all'], help="type of data to export. ")
    parser.add_argument("-c", "--clean", action="store_true", help="Clean any pre-existing output before continuing")
    parser.add_argument("-p", "--prune", action="store_true", help="Delete previous backups if any after running current backup")
    args = parser.parse_args()

    user = app.config.get("SYSTEM_USERNAME")
    job = public_data_dump.PublicDataDumpBackgroundTask.prepare(user, clean=args.clean, prune=args.prune, types=args.type)
    task = public_data_dump.PublicDataDumpBackgroundTask(job)
    BackgroundApi.execute(task)


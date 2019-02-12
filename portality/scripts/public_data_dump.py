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


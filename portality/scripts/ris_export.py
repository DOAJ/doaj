from portality.core import app
from portality.lib import dates

from portality.tasks import ris_export as asc
from portality.background import BackgroundApi
from portality.models.background import StdOutBackgroundJob


if __name__ == "__main__":
    start = dates.now()

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--force", action="store_true", help="force update of all RIS entries")
    args = parser.parse_args()

    if app.config.get("SCRIPTS_READ_ONLY_MODE", False):
        print("System is in READ-ONLY mode, enforcing read-only for this script")
        exit()

    job = asc.RISExportBackgroundTask.prepare("system", force=args.force)
    job = StdOutBackgroundJob(job)
    task = asc.RISExportBackgroundTask(job)
    BackgroundApi.execute(task)

    end = dates.now()
    print(start, "-", end)

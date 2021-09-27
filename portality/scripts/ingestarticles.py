from portality.core import app
from portality.tasks.ingestarticles import IngestArticlesBackgroundTask
from portality.background import BackgroundApi
from portality.models.background import StdOutBackgroundJob
from werkzeug import FileStorage

if __name__ == "__main__":
    if app.config.get("SCRIPTS_READ_ONLY_MODE", False):
        print("System is in READ-ONLY mode, script cannot run")
        exit()

    user = app.config.get("SYSTEM_USERNAME")

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="XML file to import")
    parser.add_argument("schema", help="doaj or crossref")
    args = parser.parse_args()

    with open(args.file) as f:
        fs = FileStorage(f, "testing.xml")
        job = IngestArticlesBackgroundTask.prepare(user, upload_file=fs, schema=args.schema)
        job = StdOutBackgroundJob(job)
        task = IngestArticlesBackgroundTask(job)
        BackgroundApi.execute(task)

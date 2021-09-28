from portality.core import app
from portality.tasks.ingestarticles import IngestArticlesBackgroundTask
from portality.background import BackgroundApi
from portality.models.background import StdOutBackgroundJob
from werkzeug import FileStorage

if __name__ == "__main__":
    if app.config.get("SCRIPTS_READ_ONLY_MODE", False):
        print("System is in READ-ONLY mode, script cannot run")
        exit()

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("username", help="username to import as")
    parser.add_argument("file", help="XML file to import")
    parser.add_argument("schema", help="doaj or crossref")
    args = parser.parse_args()

    with open(args.file, "rb") as f:
        fs = FileStorage(f, "placeholder.xml")  # fake filename required to build the FIleStorage object
        job = IngestArticlesBackgroundTask.prepare(args.username, upload_file=fs, schema=args.schema)
        job = StdOutBackgroundJob(job)
        task = IngestArticlesBackgroundTask(job)
        BackgroundApi.execute(task)

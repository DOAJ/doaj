from portality import models
from portality.lib import dates

from portality.tasks.ingestarticles import IngestArticlesBackgroundTask
from portality.tasks.suggestion_bulk_edit import SuggestionBulkEditBackgroundTask
from portality.tasks.sitemap import SitemapBackgroundTask
from portality.tasks.read_news import ReadNewsBackgroundTask
from portality.tasks.journal_csv import JournalCSVBackgroundTask


SUBMITTERS = {
    "ingest_articles" : IngestArticlesBackgroundTask,
    "suggestion_bulk_edit" : SuggestionBulkEditBackgroundTask,
    "sitemap" : SitemapBackgroundTask,
    "read_news" : ReadNewsBackgroundTask,
    "journal_csv" : JournalCSVBackgroundTask
}

def requeue_jobs(action, status, from_date, to_date):
    q = JobsQuery(action, status, from_date, to_date)

    jobs = models.BackgroundJob.q2obj(q=q.query())

    print("You are about to re-queue " + str(len(jobs)) + " jobs")
    doit = raw_input("Proceed? [Y\N]")

    if doit == "Y":
        for job in jobs:
            job.queue()
            SUBMITTERS[action].submit(job)


class JobsQuery(object):
    def __init__(self, action, status, from_date, to_date):
        self.action = action
        self.status = status
        self.from_date = from_date
        self.to_date = to_date

    def query(self):
        return {
            "query" : {
                "bool" : {
                    "must" : [
                        {"term" : {"status.exact" : self.status}},
                        {"term" : {"action.exact" : self.action}},
                        {"range" : {"created_date" : {"gte" : self.from_date, "lte" : self.to_date}}}
                    ]
                }
            },
            "size" : 10000
        }

# requeue_jobs("complete", "sitemap", None, None)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument("-s", "--status",
                        help="requeue jobs in this status",
                        default="queued")
    parser.add_argument("-a", "--action",
                        help="Background job action")
    parser.add_argument("-f", "--from_date",
                        help="Date from which to look for jobs in the given type and status",
                        default="1970-01-01T00:00:00Z")
    parser.add_argument("-t", "--to_date",
                        help="Date to which to look for jobs in the given type and status",
                        default=dates.now())
    args = parser.parse_args()

    requeue_jobs(args.action, args.status, args.from_date, args.to_date)

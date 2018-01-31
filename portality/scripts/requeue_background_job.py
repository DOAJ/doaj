"""
Script to allow us to re-queue background jobs of certain kinds.

To use, do:

python portality/scripts/requeue_background_job.py -a [action] -s [status] -f [from date] -t [to date]

-a, -s, -f and -t are optional, with the following default values:

-a : None (for running through all job types supported below, others will be skipped)
-s : queued
-f : 1970-01-01T00:00:00Z
-t : the current timestamp

Currently this script supports re-queuing the following background job types:

ingest_articles
suggestion_bulk_edit
sitemap
read_news
journal_csv

If you need to re-queue any other kind of job, you need to add it here.

FIXME: this should be a script calling functionality inside a business logic layer with a fuller understanding of jobs.
"""
from portality import models
from portality.lib import dates

from portality.tasks.ingestarticles import IngestArticlesBackgroundTask
from portality.tasks.suggestion_bulk_edit import SuggestionBulkEditBackgroundTask
from portality.tasks.sitemap import SitemapBackgroundTask
from portality.tasks.read_news import ReadNewsBackgroundTask
from portality.tasks.journal_csv import JournalCSVBackgroundTask


SUBMITTERS = {
    "ingest_articles": IngestArticlesBackgroundTask,
    "suggestion_bulk_edit": SuggestionBulkEditBackgroundTask,
    "sitemap": SitemapBackgroundTask,
    "read_news": ReadNewsBackgroundTask,
    "journal_csv": JournalCSVBackgroundTask
}


def requeue_jobs(action, status, from_date, to_date):
    q = JobsQuery(action, status, from_date, to_date)

    jobs = models.BackgroundJob.q2obj(q=q.query())

    print("You are about to re-queue " + str(len(jobs)) + " jobs")
    doit = raw_input("Proceed? [y\\N] ")

    if doit.lower() == "y":
        print("Re-queuing jobs...")
        for job in jobs:
            job.queue()
            try:
                SUBMITTERS[job.action].submit(job)
            except KeyError:
                print("This script is not set up to re-queue task type {0}. Skipping.".format(job.action))

    else:
        print("No action.")


class JobsQuery(object):
    def __init__(self, action, status, from_date, to_date):
        self.action = action
        self.status = status
        self.from_date = from_date
        self.to_date = to_date

    def query(self):
        q = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"status.exact": self.status}},
                        {"range": {"created_date": {"gte": self.from_date, "lte": self.to_date}}}
                    ]
                }
            },
            "size": 10000
        }

        if self.action is not None:
            q['query']['bool']['must'].append({"term": {"action.exact": self.action}})

        return q


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument("-s", "--status",
                        help="requeue jobs in this status",
                        default="queued")
    parser.add_argument("-a", "--action",
                        help="Background job action",
                        default=None)
    parser.add_argument("-f", "--from_date",
                        help="Date from which to look for jobs in the given type and status",
                        default="1970-01-01T00:00:00Z")
    parser.add_argument("-t", "--to_date",
                        help="Date to which to look for jobs in the given type and status",
                        default=dates.now())
    args = parser.parse_args()

    requeue_jobs(args.action, args.status, args.from_date, args.to_date)

"""
Script to allow us to re-queue or cancel background jobs of certain kinds.

To use, do:

python portality/scripts/requeue_background_job.py [-r] [-c] [-a <action>] [-s <status>] [-f <from date>] [-t <to date>]

One of -r, -c is required. -r requeues jobs, -c cancels them.
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


HANDLERS = {
    'ingest_articles': IngestArticlesBackgroundTask,
    'suggestion_bulk_edit': SuggestionBulkEditBackgroundTask,
    'sitemap': SitemapBackgroundTask,
    'read_news': ReadNewsBackgroundTask,
    'journal_csv': JournalCSVBackgroundTask
}


def manage_jobs(verb, action, status, from_date, to_date):
    q = JobsQuery(action, status, from_date, to_date)

    jobs = models.BackgroundJob.q2obj(q=q.query())

    print('You are about to {verb} {count} job(s)'.format(verb=verb, count=len(jobs)))
    doit = raw_input('Proceed? [y\\N] ')

    if doit.lower() == 'y':
        print('Please wait...')
        for job in jobs:
            if job.action not in HANDLERS:
                print('This script is not set up to {0} task type {1}. Skipping.'.format(verb, job.action))
                continue

            job.add_audit_message(u"Job {pp} from job management script.".format(
                pp={'requeue': 'requeued', 'cancel': 'cancelled'}[verb]))

            if verb == 're-queue':                                                    # Re-queue and execute immediately
                job.queue()
                HANDLERS[job.action].submit(job)
            elif verb == 'cancel':                                                         # Just apply cancelled status
                job.cancel()
                job.save()

            print('done.')
    else:
        print('No action.')


def requeue_jobs(action, status, from_date, to_date):
    manage_jobs('re-queue', action, status, from_date, to_date)


def cancel_jobs(action, status, from_date, to_date):
    manage_jobs('cancel', action, status, from_date, to_date)


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


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument('-r', '--requeue',
                        help='Add these jobs back on the job queue for processing', action='store_true')
    parser.add_argument('-c', '--cancel',
                        help='Cancel these jobs (set their status to "cancelled")', action='store_true')
    parser.add_argument('-s', '--status',
                        help='Filter for job status. Default is "queued"',
                        default='queued')
    parser.add_argument('-a', '--action',
                        help='Background job action. Leave empty for all actions (not recommended)',
                        default=None)
    parser.add_argument('-f', '--from_date',
                        help='Date from which to look for jobs in the given type and status',
                        default='1970-01-01T00:00:00Z')
    parser.add_argument('-t', '--to_date',
                        help='Date to which to look for jobs in the given type and status',
                        default=dates.now())
    args = parser.parse_args()

    if args.requeue and args.cancel:
        print('Use only --requeue OR --cancel, not both.')
        exit(1)
    elif args.requeue:
        requeue_jobs(args.action, args.status, args.from_date, args.to_date)
    elif args.cancel:
        cancel_jobs(args.action, args.status, args.from_date, args.to_date)
    else:
        print('You must supply one of --requeue or --cancel to run this script')
        exit(1)

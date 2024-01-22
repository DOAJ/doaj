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

This script supports managing the following background job types listed in HANDLERS; if you need to re-queue any other
kind of job, you need to add it there.

TODO: this should be a script calling functionality inside a business logic layer with a fuller understanding of jobs.
"""
from portality import models
from portality.lib import dates
from portality.lib.dates import DEFAULT_TIMESTAMP_VAL

from portality.tasks.anon_export import AnonExportBackgroundTask
from portality.tasks.article_bulk_delete import ArticleBulkDeleteBackgroundTask
from portality.tasks.article_bulk_create import ArticleBulkCreateBackgroundTask
from portality.tasks.article_cleanup_sync import ArticleCleanupSyncBackgroundTask
from portality.tasks.article_duplicate_report import ArticleDuplicateReportBackgroundTask
from portality.tasks.async_workflow_notifications import AsyncWorkflowBackgroundTask
from portality.tasks.check_latest_es_backup import CheckLatestESBackupBackgroundTask
# from portality.tasks.find_discontinued_soon import FindDiscontinuedSoonBackgroundTask
from portality.tasks.harvester import HarvesterBackgroundTask
from portality.tasks.ingestarticles import IngestArticlesBackgroundTask
from portality.tasks.journal_bulk_delete import JournalBulkDeleteBackgroundTask
from portality.tasks.journal_bulk_edit import JournalBulkEditBackgroundTask
from portality.tasks.journal_csv import JournalCSVBackgroundTask
from portality.tasks.journal_in_out_doaj import SetInDOAJBackgroundTask
from portality.tasks.preservation import PreservationBackgroundTask
from portality.tasks.prune_es_backups import PruneESBackupsBackgroundTask
from portality.tasks.public_data_dump import PublicDataDumpBackgroundTask
from portality.tasks.read_news import ReadNewsBackgroundTask
from portality.tasks.reporting import ReportingBackgroundTask
from portality.tasks.sitemap import SitemapBackgroundTask
from portality.tasks.suggestion_bulk_edit import SuggestionBulkEditBackgroundTask

from portality.background import BackgroundApi

# dict of {task_name: task_class} so we can interact with the jobs
HANDLERS = {
    AnonExportBackgroundTask.__action__: AnonExportBackgroundTask,
    ArticleBulkDeleteBackgroundTask.__action__: ArticleBulkDeleteBackgroundTask,
    ArticleBulkCreateBackgroundTask.__action__: ArticleBulkCreateBackgroundTask,
    ArticleCleanupSyncBackgroundTask.__action__: ArticleCleanupSyncBackgroundTask,
    ArticleDuplicateReportBackgroundTask.__action__: ArticleDuplicateReportBackgroundTask,
    AsyncWorkflowBackgroundTask.__action__: AsyncWorkflowBackgroundTask,
    CheckLatestESBackupBackgroundTask.__action__: CheckLatestESBackupBackgroundTask,
    # FindDiscontinuedSoonBackgroundTask.__action__: FindDiscontinuedSoonBackgroundTask,
    HarvesterBackgroundTask.__action__: HarvesterBackgroundTask,
    IngestArticlesBackgroundTask.__action__: IngestArticlesBackgroundTask,
    JournalBulkDeleteBackgroundTask.__action__: JournalBulkDeleteBackgroundTask,
    JournalBulkEditBackgroundTask.__action__: JournalBulkEditBackgroundTask,
    JournalCSVBackgroundTask.__action__: JournalCSVBackgroundTask,
    SetInDOAJBackgroundTask.__action__: SetInDOAJBackgroundTask,
    PreservationBackgroundTask.__action__:PreservationBackgroundTask,
    PruneESBackupsBackgroundTask.__action__: PruneESBackupsBackgroundTask,
    PublicDataDumpBackgroundTask.__action__: PublicDataDumpBackgroundTask,
    ReadNewsBackgroundTask.__action__: ReadNewsBackgroundTask,
    ReportingBackgroundTask.__action__: ReportingBackgroundTask,
    SitemapBackgroundTask.__action__: SitemapBackgroundTask,
    SuggestionBulkEditBackgroundTask.__action__: SuggestionBulkEditBackgroundTask
}


def manage_jobs(verb, action, status, from_date, to_date, prompt=True):
    q = JobsQuery(action, status, from_date, to_date)

    jobs = models.BackgroundJob.q2obj(q=q.query())

    print('You are about to {verb} {count} job(s)'.format(verb=verb, count=len(jobs)))

    doit = "y"
    if prompt:
        doit = input('Proceed? [y\\N] ')

    if doit.lower() == 'y':
        print('Please wait...')
        for job in jobs:
            if job.action not in HANDLERS:
                print('This script is not set up to {0} task type {1}. Skipping.'.format(verb, job.action))
                continue

            job.add_audit_message("Job {pp} from job management script.".format(
                pp={'requeue': 'requeued', 'cancel': 'cancelled', "process": "processed"}[verb]))

            if verb == 'requeue':                                                     # Re-queue and execute immediately
                job.queue()
                HANDLERS[job.action].submit(job)
            elif verb == 'cancel':                                                         # Just apply cancelled status
                job.cancel()
                job.save()
            elif verb == 'process':
                task = HANDLERS[job.action](job)    # Just execute immediately without going through huey
                BackgroundApi.execute(task)

            print('done.')
    else:
        print('No action.')


def requeue_jobs(action, status, from_date, to_date, prompt=True):
    manage_jobs('requeue', action, status, from_date, to_date, prompt=prompt)


def cancel_jobs(action, status, from_date, to_date, prompt=True):
    manage_jobs('cancel', action, status, from_date, to_date, prompt=prompt)

def process_jobs(action, status, from_date, to_date, prompt=True):
    manage_jobs("process", action, status, from_date, to_date, prompt=prompt)


class JobsQuery(object):
    def __init__(self, action, status, from_date, to_date):
        self.action = action
        self.status = status
        self.from_date = from_date
        self.to_date = to_date

    def query(self):
        q = {
            "track_total_hits": True,
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
    parser.add_argument("-p", "--process",
                        help="Immediately process these jobs on the command line", action="store_true")
    parser.add_argument('-s', '--status',
                        help='Filter for job status. Default is "queued"',
                        default='queued')
    parser.add_argument('-a', '--action',
                        help='Background job action. Leave empty for all actions (not recommended)',
                        default=None)
    parser.add_argument('-f', '--from_date',
                        help='Date from which to look for jobs in the given type and status',
                        default=DEFAULT_TIMESTAMP_VAL)
    parser.add_argument('-t', '--to_date',
                        help='Date to which to look for jobs in the given type and status',
                        default=dates.now_str())
    parser.add_argument("-y", "--yes", help="Answer yes to all prompts", action="store_true")
    args = parser.parse_args()

    if args.requeue and args.cancel:
        print('Use only --requeue OR --cancel, not both.')
        exit(1)
    elif args.requeue:
        requeue_jobs(args.action, args.status, args.from_date, args.to_date, prompt=False if args.yes else True)
    elif args.cancel:
        cancel_jobs(args.action, args.status, args.from_date, args.to_date, prompt=False if args.yes else True)
    elif args.process:
        process_jobs(args.action, args.status, args.from_date, args.to_date, prompt=False if args.yes else True)
    else:
        print('You must supply one of --requeue, --cancel or --process to run this script')
        exit(1)

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
import argparse
import json
from typing import Dict, Type, List

from portality import models
from portality.background import BackgroundApi, BackgroundTask
from portality.lib import dates
from portality.lib.dates import DEFAULT_TIMESTAMP_VAL
from portality.tasks.anon_export import AnonExportBackgroundTask
from portality.tasks.article_bulk_delete import ArticleBulkDeleteBackgroundTask
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

# dict of {task_name: task_class} so we can interact with the jobs
HANDLERS: Dict[str, Type[BackgroundTask]] = {
    AnonExportBackgroundTask.__action__: AnonExportBackgroundTask,
    ArticleBulkDeleteBackgroundTask.__action__: ArticleBulkDeleteBackgroundTask,
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
    PreservationBackgroundTask.__action__: PreservationBackgroundTask,
    PruneESBackupsBackgroundTask.__action__: PruneESBackupsBackgroundTask,
    PublicDataDumpBackgroundTask.__action__: PublicDataDumpBackgroundTask,
    ReadNewsBackgroundTask.__action__: ReadNewsBackgroundTask,
    ReportingBackgroundTask.__action__: ReportingBackgroundTask,
    SitemapBackgroundTask.__action__: SitemapBackgroundTask,
    SuggestionBulkEditBackgroundTask.__action__: SuggestionBulkEditBackgroundTask
}


def handle_requeue(job: models.BackgroundJob):
    if job.action not in HANDLERS:
        print('This script is not set up to {0} task type {1}. Skipping.'.format('requeue', job.action))
        return

    job.queue()
    HANDLERS[job.action].submit(job)


def handle_cancel(job: models.BackgroundJob):
    job.cancel()
    job.save()


def handle_process(job: models.BackgroundJob):
    if job.action not in HANDLERS:
        print('This script is not set up to {0} task type {1}. Skipping.'.format('process', job.action))
        return

    task = HANDLERS[job.action](job)  # Just execute immediately without going through huey
    BackgroundApi.execute(task)


cmd_handlers = {
    'requeue': handle_requeue,
    'cancel': handle_cancel,
    'process': handle_process,
}


def manage_jobs(verb, action, status, from_date, to_date, prompt=True, size=10000):
    q = JobsQuery(action, status, from_date, to_date, size=size)

    jobs: List[models.BackgroundJob] = models.BackgroundJob.q2obj(q=q.query())
    if len(jobs) == 0:
        print('No jobs found by query: ')
        print(json.dumps(q.query(), indent=4))
        return

    print('You are about to {verb} {count} job(s)'.format(verb=verb, count=len(jobs)))
    print('The first 5 are:')
    for j in jobs[:5]:
        print(f'Id: {j.id}, Status: {j.status}, Action: {j.action}, Created: {j.created_date}')

    doit = "y"
    if prompt:
        doit = input('Proceed? [y\\N] ')

    if doit.lower() != 'y':
        print('No action.')
        return

    job_handler = cmd_handlers.get(verb)
    if job_handler is None:
        print(f'Unknown verb: {verb}')
        return

    print('Please wait...')
    for job in jobs:
        job.add_audit_message("Job [{pp}] from job management script.".format(
            pp={'requeue': 'requeued', 'cancel': 'cancelled', "process": "processed"}[verb]))
        job_handler(job)

    print('done.')


class JobsQuery(object):
    def __init__(self, action, status, from_date, to_date, size=10000):
        self.action = action
        self.status = status
        self.from_date = from_date
        self.to_date = to_date
        self.size = size

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
            "size": self.size
        }

        if self.action is not None:
            q['query']['bool']['must'].append({"term": {"action.exact": self.action}})

        return q


def add_common_arguments(parser: argparse.ArgumentParser):
    # common options
    parser.add_argument("-y", "--yes", help="Answer yes to all prompts", action="store_true")

    # query options
    query_options = parser.add_argument_group('Query options')

    query_options.add_argument('-s', '--status',
                               help='Filter for job status. Default is "queued"',
                               default='queued')
    query_options.add_argument('-a', '--action',
                               help='Background job action. Leave empty for all actions (not recommended)',
                               default=None)
    query_options.add_argument('-f', '--from_date',
                               help='Date from which to look for jobs in the given type and status',
                               default=DEFAULT_TIMESTAMP_VAL)
    query_options.add_argument('-t', '--to_date',
                               help='Date to which to look for jobs in the given type and status',
                               default=dates.now_str()
                               )

    default_size = 10000
    query_options.add_argument('--size',
                               help=f'Number of jobs to process at a time, default is {default_size}',
                               type=int, default=default_size, )


def main():
    parser = argparse.ArgumentParser(description='Manage background jobs in the DOAJ database and redis')
    sp = parser.add_subparsers(dest='cmdname', help='Actions')

    sp_p = sp.add_parser('requeue', help='Add these jobs back on the job queue for processing')
    add_common_arguments(sp_p)

    sp_p = sp.add_parser('cancel', help='Cancel these jobs (set their status to "cancelled")')
    add_common_arguments(sp_p)

    sp_p = sp.add_parser('process', help='Immediately process these jobs on the command line')
    add_common_arguments(sp_p)

    args = parser.parse_args()

    cmdname = args.__dict__.get('cmdname')
    if cmdname in ['requeue', 'cancel', 'process']:
        manage_jobs(cmdname,
                    args.action, args.status,
                    args.from_date, args.to_date,
                    prompt=not args.yes)
    else:
        parser.print_help()
        exit(1)


if __name__ == '__main__':
    main()

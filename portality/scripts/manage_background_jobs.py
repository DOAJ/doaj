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
import itertools
import re
import argparse
import json
import pickle
import typing
from typing import Dict, Type, List
from collections import Counter

from portality.constants import BGJOB_STATUS_COMPLETE, BGJOB_STATUS_ERROR
from portality.lib import dates, color_text, es_queries
from portality.lib.dates import DEFAULT_TIMESTAMP_VAL

if typing.TYPE_CHECKING:
    from portality.models import BackgroundJob


def get_action_handler(action):
    from portality.background import BackgroundTask
    from portality.tasks.anon_export import AnonExportBackgroundTask
    from portality.tasks.article_bulk_delete import ArticleBulkDeleteBackgroundTask
    from portality.tasks.article_cleanup_sync import ArticleCleanupSyncBackgroundTask
    from portality.tasks.article_duplicate_report import ArticleDuplicateReportBackgroundTask
    from portality.tasks.async_workflow_notifications import AsyncWorkflowBackgroundTask
    from portality.tasks.check_latest_es_backup import CheckLatestESBackupBackgroundTask
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
    return HANDLERS.get(action)


def handle_requeue(job: 'BackgroundJob'):
    handler = get_action_handler(job.action)
    if handler is None:
        print('This script is not set up to {0} task type {1}. Skipping.'.format('requeue', job.action))
        return

    job.queue()
    handler.submit(job)


def handle_cancel(job: 'BackgroundJob'):
    job.cancel()
    job.save()


def handle_process(job: 'BackgroundJob'):
    from portality.background import BackgroundApi
    handler = get_action_handler(job.action)
    if handler is None:
        print('This script is not set up to {0} task type {1}. Skipping.'.format('process', job.action))
        return

    task = handler(job)  # Just execute immediately without going through huey
    BackgroundApi.execute(task)


cmd_handlers = {
    'requeue': handle_requeue,
    'cancel': handle_cancel,
    'process': handle_process,
}


def manage_jobs(verb, action, status, from_date, to_date, prompt=True, size=10000):
    from portality import models
    q = JobsQuery(action, status, from_date, to_date, size=size)

    jobs: List[models.BackgroundJob] = models.BackgroundJob.q2obj(q=q.query())
    if len(jobs) == 0:
        print('No jobs found by query: ')
        print(json.dumps(q.query(), indent=4))
        return

    print('You are about to {verb} {count} job(s)'.format(verb=verb, count=len(jobs)))
    print('The first 5 are:')
    for j in jobs[:5]:
        print(job_to_str(j))

    if prompt and input('Proceed? [y\\N] ').lower() != 'y':
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


def job_to_str(job: 'BackgroundJob'):
    return f'{job.action:30} {job.id} {job.status:10} {job.created_date}'


def add_arguments_yes(parser: argparse.ArgumentParser):
    parser.add_argument("-y", "--yes", help="Answer yes to all prompts", action="store_true")


def add_arguments_common(parser: argparse.ArgumentParser):
    # common options
    add_arguments_yes(parser)

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


def create_redis_client():
    import redis
    from portality.core import app
    client = redis.StrictRedis(host=app.config['HUEY_REDIS_HOST'], port=app.config['HUEY_REDIS_PORT'], db=0)
    return client


class HueyJobData:

    def __init__(self, data: tuple):
        self.data = data
        self.huey_id, self.queue_name, self.schedule_time, self.retries, self.retry_delay, self.args, *_ = data

    @property
    def is_scheduled(self):
        return self.schedule_time is None

    @property
    def bgjob_name(self):
        return re.sub(r'^queue_task_(scheduled_)?', '', self.queue_name)

    @property
    def bgjob_id(self):
        if self.args:
            return self.args[0][0]
        return None

    @classmethod
    def from_redis(cls, redis_row):
        return HueyJobData(pickle.loads(redis_row))


def print_huey_jobs_counter(counter):
    for k, v in sorted(counter.items(), key=lambda x: x[0]):
        print(f'{k:30} {v}')


def print_huey_job_data(job_data: HueyJobData):
    print(f'{job_data.bgjob_name:30} {job_data.bgjob_id} {dates.format(job_data.schedule_time)}')


def report(example_size=10):
    client = create_redis_client()
    huey_rows = itertools.chain.from_iterable((client.lrange(k, 0, -1)
                                               for k in ['huey.redis.doajmainqueue', 'huey.redis.doajlongrunning', ]))
    huey_rows = (HueyJobData.from_redis(r) for r in huey_rows)
    huey_rows = list(huey_rows)

    scheduled = Counter(r.bgjob_name for r in huey_rows if r.is_scheduled)
    unscheduled = Counter(r.bgjob_name for r in huey_rows if not r.is_scheduled)

    print('# Huey jobs:')
    print('### Scheduled:')
    print_huey_jobs_counter(scheduled)
    print()

    print('### Unscheduled:')
    print_huey_jobs_counter(unscheduled)
    print()

    print(f'### last {example_size} unscheduled jobs:')
    unscheduled_jobs = sorted((r for r in huey_rows if not r.is_scheduled),
                              key=lambda x: x.schedule_time, reverse=True)
    for r in unscheduled_jobs[:example_size]:
        print_huey_job_data(r)
    print()

    print('# DB records:')
    from portality import models
    from portality.models.background import BackgroundJobQueryBuilder
    bgjobs: List[BackgroundJob] = models.BackgroundJob.q2obj(
        q=BackgroundJobQueryBuilder()
        .status_excludes([BGJOB_STATUS_COMPLETE, BGJOB_STATUS_ERROR])
        .build_query_dict())

    print('### Summary')
    counter = Counter((j.action, j.status) for j in bgjobs)
    for k, v in sorted(counter.items(), key=lambda x: x[0]):
        print(f'{k[0]:30} {k[1]:10} {v}')
    print()

    print(f'### last {example_size} jobs:')
    for j in sorted(bgjobs, key=lambda j: j.created_date, reverse=True)[:example_size]:
        print(job_to_str(j))
    print()


def clean_all():
    if input(color_text.apply_color(
            'WARNING: This will delete all jobs from redis and the database. Proceed? [y\\N] ',
            background=color_text.Color.red)).lower() != 'y':
        print('No action.')
        return
    from portality import models

    print('Remove all jobs from DB')
    models.BackgroundJob.delete_by_query(es_queries.query_all())

    print('Remove all jobs from redis')
    client = create_redis_client()
    client.delete('huey.redis.doajmainqueue')
    client.delete('huey.redis.doajlongrunning')


def main():
    parser = argparse.ArgumentParser(description='Manage background jobs in the DOAJ database and redis')
    sp = parser.add_subparsers(dest='cmdname', help='Actions', )

    sp_p = sp.add_parser('requeue', help='Add these jobs back on the job queue for processing')
    add_arguments_common(sp_p)

    sp_p = sp.add_parser('cancel', help='Cancel these jobs (set their status to "cancelled")')
    add_arguments_common(sp_p)

    sp_p = sp.add_parser('process', help='Immediately process these jobs on the command line')
    add_arguments_common(sp_p)

    sp_p = sp.add_parser('report', help='Report status of jobs, e.g. out sync job on redis and db ')

    sp_p = sp.add_parser('clean-all', help='Remove all Jobs from redis and DB')

    args = parser.parse_args()

    cmdname = args.__dict__.get('cmdname')
    if cmdname in ['requeue', 'cancel', 'process']:
        manage_jobs(cmdname,
                    args.action, args.status,
                    args.from_date, args.to_date,
                    prompt=not args.yes)
    elif cmdname == 'report':
        report()
    elif cmdname == 'clean-all':
        clean_all()
    else:
        parser.print_help()
        exit(1)


if __name__ == '__main__':
    main()
    # report()

"""
Script to allow us to re-queue or cancel background jobs of certain kinds.

This script supports managing the following background job types listed in HANDLERS; if you need to re-queue any other
kind of job, you need to add it there.

TODO: this should be a script calling functionality inside a business logic layer with a fuller understanding of jobs.
"""
import argparse
import json
import time
import typing
from collections import Counter
from typing import Dict, Type, List

from portality import constants
from portality.constants import BGJOB_STATUS_QUEUED
from portality.lib import dates, color_text, es_queries
from portality.lib.dates import DEFAULT_TIMESTAMP_VAL

if typing.TYPE_CHECKING:
    from portality.models import BackgroundJob
    from portality.bll.services.huey_job import HueyJobData


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


def manage_jobs(verb, action, status, from_date, to_date, job_id, prompt=True, size=10000):
    from portality import models
    if job_id is not None:
        j = models.BackgroundJob.pull(job_id)
        jobs: List[models.BackgroundJob] = [] if j is None else [j]
        query_ref = job_id
    else:
        q = JobsQuery(action, status, from_date, to_date, size=size)
        jobs: List[models.BackgroundJob] = models.BackgroundJob.q2obj(q=q.query())
        query_ref = json.dumps(q.query(), indent=4)

    if len(jobs) == 0:
        print('No jobs found by query: ')
        print(query_ref)
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


def find_bgjobs_by_status(status) -> List['BackgroundJob']:
    from portality import models
    bgjobs = models.BackgroundJob.q2obj(
        q=models.background.BackgroundJobQueryBuilder()
        .status_includes([status])
        .size(10000)
        .build_query_dict())
    return bgjobs


def job_to_str(job: 'BackgroundJob'):
    return f'{job.action:30} {job.id} {job.status:10} {job.created_date}'


def print_huey_jobs_counter(counter):
    for k, v in sorted(counter.items(), key=lambda x: x[0]):
        print(f'{k:30} {v}')


def print_huey_job_data(job_data: 'HueyJobData'):
    print(f'{job_data.bgjob_action:30} {job_data.bgjob_id} {dates.format(job_data.schedule_time)}')


def print_job_delta(title_val, id_action_list: typing.Iterable[tuple]):
    id_action_list = sorted(id_action_list, key=lambda x: x[1])
    print(title(f'{title_val} ({len(id_action_list)})'))
    for id, action in id_action_list:
        print(f'{action:30} {id}')
    print()


def total_counter(counter):
    return sum(counter.values())


def title(s):
    return color_text.apply_color(s, front=color_text.Color.black, background=color_text.Color.green)


def report(example_size=10):
    from portality.bll.services.huey_job import huey_job_service
    huey_rows = list(huey_job_service.find_all_huey_jobs())

    scheduled = Counter(r.bgjob_action for r in huey_rows if r.is_scheduled)
    unscheduled = Counter(r.bgjob_action for r in huey_rows if not r.is_scheduled)

    print(title('# Huey jobs:'))
    print(title(f'### Scheduled ({total_counter(scheduled)})'))
    print_huey_jobs_counter(scheduled)
    print()

    print(title(f'### Unscheduled ({total_counter(unscheduled)})'))
    print_huey_jobs_counter(unscheduled)
    print()

    print(title(f'### last {example_size} unscheduled jobs:'))
    unscheduled_huey_jobs = sorted((r for r in huey_rows if not r.is_scheduled),
                                   key=lambda x: x.schedule_time, reverse=True)
    for r in unscheduled_huey_jobs[:example_size]:
        print_huey_job_data(r)
    print()

    counter = Counter(r.bgjob_id for r in huey_rows if not r.is_scheduled)
    counter = {k: v for k, v in counter.items() if v > 1}
    if counter:
        print(title(f'### Duplicated jobs ({total_counter(counter)})'))
        for k, v in counter.items():
            print(f'{k} {v}')

    print_huey_jobs_counter(counter)

    print(title('# DB records'))
    print(title(f'### Processing'))
    for j in find_bgjobs_by_status(constants.BGJOB_STATUS_PROCESSING):
        print(job_to_str(j))
    print()

    bgjobs: List[BackgroundJob] = find_bgjobs_by_status(BGJOB_STATUS_QUEUED)
    counter = Counter((j.action, j.status) for j in bgjobs)
    print(title(f'### Queued ({sum(counter.values())})'))
    for k, v in sorted(counter.items(), key=lambda x: x[0]):
        print(f'{k[0]:30} {k[1]:10} {v}')
    print()

    print(title(f'### last {example_size} jobs'))
    for j in sorted(bgjobs, key=lambda j: j.created_date, reverse=True)[:example_size]:
        print(job_to_str(j))
    print()

    print(title('# Queued delta between DB and redis:'))
    huey_only, db_only = find_huey_bgjob_delta(unscheduled_huey_jobs, bgjobs)
    print_job_delta('### DB only', ((j.id, j.action) for j in db_only))
    print_job_delta('### Redis only', ((i.bgjob_id, i.bgjob_action) for i in huey_only))


def rm_all():
    from portality.bll.services.huey_job import huey_job_service
    if input(color_text.apply_color(
            'WARNING: This will delete all jobs from redis and the database. Proceed? [y\\N] ',
            background=color_text.Color.red)).lower() != 'y':
        print('No action.')
        return
    from portality import models

    print('Remove all jobs from DB')
    models.BackgroundJob.delete_by_query(es_queries.query_all())

    print('Remove all jobs from redis')
    client = huey_job_service.create_redis_client()
    client.delete('huey.redis.doajmainqueue')
    client.delete('huey.redis.doajlongrunning')


def rm_old_processing(is_all=False):
    from portality import models
    from portality.constants import BGJOB_STATUS_PROCESSING
    from portality.models.background import BackgroundJobQueryBuilder

    bgjobs = models.BackgroundJob.q2obj(q=BackgroundJobQueryBuilder()
                                        .status_includes([BGJOB_STATUS_PROCESSING])
                                        .order_by('created_date', 'asc')
                                        .size(10000)
                                        .build_query_dict())

    if not is_all:
        bgjobs = bgjobs[:-1]

    if bgjobs:
        print(f'Following {len(bgjobs)} jobs will be removed:')
        for j in bgjobs:
            print(job_to_str(j))
        models.BackgroundJob.bulk_delete(b.id for b in bgjobs)


def rm_redundant():
    from portality.core import app
    from portality import models
    from portality.bll.services.huey_job import huey_job_service

    target_actions = app.config.get('BGJOB_MANAGE_REDUNDANT_ACTIONS', [])
    print(f'Following actions will be cleaned up for redundant jobs: {target_actions}')
    client = huey_job_service.create_redis_client()
    huey_rows = list(huey_job_service.find_queued_huey_jobs())
    for action in target_actions:
        bgjobs = models.BackgroundJob.q2obj(q=models.background.BackgroundJobQueryBuilder()
                                            .status_includes([BGJOB_STATUS_QUEUED])
                                            .action(action)
                                            .order_by('created_date', 'asc')
                                            .size(10000)
                                            .build_query_dict())
        bgjobs = bgjobs[:-1]
        if not bgjobs:
            continue

        print(f'Remove redundant jobs: [{action}][{len(bgjobs)}]')
        # remove from db
        models.BackgroundJob.bulk_delete(b.id for b in bgjobs)

        # remove from redis
        for j in bgjobs:
            for h in iter(huey_rows):
                if h.bgjob_id == j.id:
                    rm_huey_job_from_redis(client, h)
                    huey_rows.remove(h)
                    break


def find_huey_bgjob_delta(huey_rows: List['HueyJobData'] = None,
                          bgjobs: List['BackgroundJob'] = None
                          ) -> (List['HueyJobData'], List['BackgroundJob']):
    from portality.bll.services.huey_job import huey_job_service
    huey_rows: List['HueyJobData'] = (list(huey_job_service.find_queued_huey_jobs())
                                      if huey_rows is None else list(huey_rows))
    bgjobs: List[BackgroundJob] = (find_bgjobs_by_status(BGJOB_STATUS_QUEUED)
                                   if bgjobs is None else list(bgjobs))

    huey_ids = {i.bgjob_id for i in huey_rows}
    db_ids = {j.id for j in bgjobs}

    huey_only = [i for i in huey_rows if i.bgjob_id not in db_ids]
    db_only = [j for j in bgjobs if j.id not in huey_ids]
    return huey_only, db_only


def rm_async_queued_jobs():
    from portality.bll.services.huey_job import huey_job_service
    huey_only, db_only = find_huey_bgjob_delta()
    print('Remove async queued jobs')
    print_job_delta('### DB only', ((j.id, j.action) for j in db_only))
    if db_only:
        from portality import models
        models.BackgroundJob.bulk_delete(d.id for d in db_only)

    print_job_delta('### Redis only', ((i.bgjob_id, i.bgjob_action) for i in huey_only))
    client = huey_job_service.create_redis_client()
    for i in huey_only:
        rm_huey_job_from_redis(client, i)


def rm_huey_job_from_redis(redis_client, huey_job_data: 'HueyJobData'):
    for key in ['huey.redis.doajmainqueue', 'huey.redis.doajlongrunning']:
        if redis_client.lrem(key, 1, huey_job_data.as_redis()):
            break


def cleanup():
    rm_redundant()
    rm_old_processing()

    time.sleep(5)  # wait DB records to be deleted
    rm_async_queued_jobs()


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
    query_options.add_argument('-i', '--id',
                               help='Background Job id',
                               default=None)

    default_size = 10000
    query_options.add_argument('--size',
                               help=f'Number of jobs to process at a time, default is {default_size}',
                               type=int, default=default_size, )


def main():
    epilog = """
    
Example
------------

### Requeue all 'read_news' jobs from 1970-01-0 to 2020-01-01
manage-bgjobs requeue -a read_news -f 1970-01-01T00:00:00Z -t 2020-01-01T00:00:00Z

### Cancel job with id abcd12 without confirmation prompt
manage-bgjobs cancel -i abcd12 -y

### cleanup outdated jobs
manage-bgjobs cleanup
    
    """

    parser = argparse.ArgumentParser(description='Manage background jobs in the DOAJ database and redis',
                                     epilog=epilog,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = parser.add_subparsers(dest='cmdname', help='Actions', )

    sp_p = sp.add_parser('requeue', help='Add these jobs back on the job queue for processing')
    add_arguments_common(sp_p)

    sp_p = sp.add_parser('cancel', help='Cancel these jobs (set their status to "cancelled")')
    add_arguments_common(sp_p)

    sp_p = sp.add_parser('process', help='Immediately process these jobs on the command line')
    add_arguments_common(sp_p)

    sp_p = sp.add_parser('report', help='Report status of jobs, e.g. out sync job on redis and db ')

    sp_p = sp.add_parser('rm-all', help='Remove all Jobs from redis and DB')

    sp_p = sp.add_parser('cleanup',
                         help=('Remove all outdated / async records, include old processing job,'
                               'redundant queued jobs, async queued jobs'))

    args = parser.parse_args()

    cmdname = args.__dict__.get('cmdname')
    if cmdname in ['requeue', 'cancel', 'process']:
        manage_jobs(cmdname,
                    args.action, args.status,
                    args.from_date, args.to_date,
                    job_id=args.id,
                    prompt=not args.yes)
    elif cmdname == 'report':
        report()
    elif cmdname == 'rm-all':
        rm_all()
    elif cmdname == 'cleanup':
        cleanup()
    else:
        parser.print_help()
        exit(1)


if __name__ == '__main__':
    main()
    # report()

import datetime
from typing import Type

from portality.background import BackgroundTask
from portality.core import app
from portality.dao import DomainObject
from portality.decorators import write_required
from portality.lib import dates
from portality.lib.es_queries import ES_DATETIME_FMT
from portality.models import Notification, BackgroundJob
from portality.tasks.helpers import background_helper
from portality.tasks.redis_huey import schedule, long_running

target_queue = long_running


class RetentionQuery:
    def __init__(self,
                 last_retention_date: datetime.datetime,
                 datetime_field='created_date'):
        self.last_retention_date = last_retention_date
        self.datetime_field = datetime_field

    def query(self):
        # returns the query dict
        return {
            'query': {
                'range': {
                    self.datetime_field: {
                        'lte': self.last_retention_date.strftime(ES_DATETIME_FMT),
                    }
                }
            }
        }


def _clean_old_data(domain_class: Type[DomainObject],
                    datetime_field='created_date',
                    logger_fn=None, ):
    if logger_fn is None:
        logger_fn = print

    n_retention_day = app.config.get("TASK_DATA_RETENTION_DAYS", {}).get(domain_class.__type__, 180)
    if not n_retention_day or n_retention_day <= 0:
        logger_fn(f'stop cleanup for invalid retention_day [{domain_class.__type__}][{n_retention_day}]')
        return

    logger_fn(f'working for clean_old_data [{domain_class.__type__}][{n_retention_day}]')

    last_retention_date = dates.now() - datetime.timedelta(days=n_retention_day)
    retention_query = RetentionQuery(last_retention_date, datetime_field=datetime_field).query()
    num_record = domain_class.hit_count(retention_query)
    logger_fn(f'remove [{domain_class.__name__}] -- {datetime_field} <= {last_retention_date}')
    logger_fn(f'number of [{domain_class.__name__}][{num_record}] to be removed.')
    domain_class.delete_by_query(retention_query)


def clean_all_old_data(logger_fn=None):
    if logger_fn is None:
        logger_fn = print

    for klazz in [Notification, BackgroundJob]:
        _clean_old_data(klazz, logger_fn=logger_fn)
    logger_fn("old data cleanup completed")


class OldDataCleanupBackgroundTask(BackgroundTask):
    __action__ = "old_data_cleanup"

    def run(self):
        kwargs = {'logger_fn': self.background_job.add_audit_message}
        clean_all_old_data(**kwargs)

    def cleanup(self):
        pass

    @classmethod
    def prepare(cls, username, **kwargs):
        return background_helper.create_job(username=username,
                                            action=cls.__action__)

    @classmethod
    def submit(cls, background_job):
        background_helper.submit_by_background_job(
            background_job, execute_old_data_cleanup
        )


@target_queue.periodic_task(schedule(OldDataCleanupBackgroundTask.__action__))
@write_required(script=True)
def scheduled_old_data_cleanup():
    background_helper.submit_by_bg_task_type(OldDataCleanupBackgroundTask)


execute_old_data_cleanup = background_helper.create_execute_fn(
    target_queue, OldDataCleanupBackgroundTask
)

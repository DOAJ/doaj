import datetime
from typing import Type

from portality.background import BackgroundTask
from portality.core import app
from portality.dao import DomainObject
from portality.decorators import write_required
from portality.lib.es_queries import ES_DATETIME_FMT
from portality.models import Notification, BackgroundJob
from portality.tasks.helpers import background_helper
from portality.tasks.redis_huey import schedule, long_running

target_queue = long_running


def _clean_old_data(domain_class: Type[DomainObject], retention_days,
                    datetime_field='created_date',
                    logger_fn=None, ):
    if logger_fn is None:
        logger_fn = print

    last_retention_date = datetime.datetime.now() - datetime.timedelta(days=retention_days)
    query = {
        'query': {
            'range': {
                datetime_field: {
                    'lte': last_retention_date.strftime(ES_DATETIME_FMT),
                }
            }
        }
    }

    num_record = domain_class.hit_count(query)
    logger_fn(f'remove [{domain_class.__name__}] -- {datetime_field} <= {last_retention_date}')
    logger_fn(f'number of [{domain_class.__name__}][{num_record}] to be remove.')
    domain_class.delete_by_query(query)


def clean_all_old_data(bgjob_retention_days=180,
                       noti_retention_days=180,
                       logger_fn=None):
    if logger_fn is None:
        logger_fn = print

    _clean_old_data(Notification, noti_retention_days, logger_fn=logger_fn)
    _clean_old_data(BackgroundJob, bgjob_retention_days, logger_fn=logger_fn)
    logger_fn("old data cleanup completed")


class OldDataCleanupBackgroundTask(BackgroundTask):
    __action__ = "old_data_cleanup"

    def run(self):
        kwargs = self.create_raw_param_dict(self.background_job.params,
                                            ['bgjob_retention_days',
                                             'noti_retention_days', ])
        kwargs['logger_fn'] = self.background_job.add_audit_message

        clean_all_old_data(**kwargs)

    def cleanup(self):
        pass

    @classmethod
    def prepare(cls, username, **kwargs):
        params = cls.create_job_params(
            bgjob_retention_days=background_helper.get_value_safe('bgjob_retention_days', 6, kwargs),
            noti_retention_days=background_helper.get_value_safe('noti_retention_days', 6, kwargs),
        )
        return background_helper.create_job(username=username,
                                            action=cls.__action__,
                                            params=params)

    @classmethod
    def submit(cls, background_job):
        background_helper.submit_by_background_job(
            background_job, execute_old_data_cleanup
        )


@target_queue.periodic_task(schedule(OldDataCleanupBackgroundTask.__action__))
@write_required(script=True)
def scheduled_old_data_cleanup():
    background_helper.submit_by_bg_task_type(OldDataCleanupBackgroundTask,
                                             bgjob_retention_days=app.config.get("TASKS_BGJOB_RETENTION_DAYS"),
                                             noti_retention_days=app.config.get("TASKS_NOTIFICATION_RETENTION_DAYS"),
                                             )


execute_old_data_cleanup = background_helper.create_execute_fn(
    target_queue, OldDataCleanupBackgroundTask
)

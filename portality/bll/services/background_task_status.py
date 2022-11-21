"""
~~BackgroundTask:MonitoringStatus~~
"""
import itertools
from typing import Iterable

from portality.constants import BGJOB_QUEUE_TYPE_LONG, BGJOB_QUEUE_TYPE_MAIN, BGJOB_STATUS_ERROR, BGJOB_STATUS_QUEUED, \
    BG_STATUS_STABLE, BG_STATUS_UNSTABLE
from portality.core import app
from portality.lib import dates
from portality.models.background import BackgroundJobQueryBuilder, BackgroundJob, SimpleBgjobQueue, \
    LastCompletedJobQuery
from portality.tasks.helpers import background_helper


class BackgroundTaskStatusService:
    """
    "background_task_status" is concept for list current background task status for monitoring.
    `create_background_status` is important function in service for create background_status data
    """

    def is_stable(self, val):
        return val == BG_STATUS_STABLE

    def to_bg_status_str(self, stable_val: bool) -> str:
        return BG_STATUS_STABLE if stable_val else BG_STATUS_UNSTABLE

    def all_stable(self, items: Iterable, field_name='status') -> bool:
        return all(self.is_stable(q.get(field_name)) for q in items)

    def all_stable_str(self, items: Iterable, field_name='status') -> str:
        return self.to_bg_status_str(self.all_stable(items, field_name))

    def create_errors_status(self, action, check_sec=3600, allowed_num_err=0, **_) -> dict:
        in_monitoring_query = SimpleBgjobQueue(action, status=BGJOB_STATUS_ERROR, since=dates.before_now(check_sec))
        num_err_in_monitoring = BackgroundJob.hit_count(query=in_monitoring_query.query())

        # prepare errors messages
        err_msgs = []
        if num_err_in_monitoring > allowed_num_err:
            err_msgs.append(f'too many error in monitoring period [{num_err_in_monitoring} > {allowed_num_err}]')

        return dict(
            status=self.to_bg_status_str(not err_msgs),
            total=BackgroundJob.hit_count(query=SimpleBgjobQueue(action, status=BGJOB_STATUS_ERROR).query()),
            in_monitoring_period=num_err_in_monitoring,
            err_msgs=err_msgs,
        )

    def create_queued_status(self, action, total=2, oldest=1200, **_) -> dict:
        total_queued = BackgroundJob.hit_count(query=SimpleBgjobQueue(action, status=BGJOB_STATUS_QUEUED).query())
        oldest_query = (BackgroundJobQueryBuilder().action(action)
                        .status_includes(BGJOB_STATUS_QUEUED).size(1)
                        .order_by('created_date', 'asc')
                        .build_query_dict())
        oldest_jobs = list(BackgroundJob.q2obj(q=oldest_query))
        oldest_job = oldest_jobs and oldest_jobs[0]

        err_msgs = []
        limited_oldest_date = dates.before_now(oldest)
        if oldest_job and oldest_job.created_timestamp < limited_oldest_date:
            err_msgs.append('outdated job found. created_timestamp[{} < {}]'.format(
                oldest_job.created_timestamp,
                limited_oldest_date
            ))

        if total_queued > total:
            err_msgs.append(f'too many queued job [{total_queued} > {total}]')

        return dict(
            status=self.to_bg_status_str(not err_msgs),
            total=total_queued,
            oldest=oldest_job.created_date if oldest_job else None,
            err_msgs=err_msgs,
        )

    def create_queues_status(self, queue_name) -> dict:
        # define last_completed_job
        bgjob_list = BackgroundJob.q2obj(q=LastCompletedJobQuery(queue_name).query())
        bgjob_list = list(bgjob_list)
        if bgjob_list:
            last_completed_date = bgjob_list[0].last_updated_timestamp
        else:
            last_completed_date = None

        errors = {action: self.create_errors_status(action, **config) for action, config
                  in self.get_config_dict_by_queue_name('BG_MONITOR_ERRORS_CONFIG', queue_name).items()}

        queued = {action: self.create_queued_status(action, **config) for action, config
                  in self.get_config_dict_by_queue_name('BG_MONITOR_QUEUED_CONFIG', queue_name).items()}

        # prepare for err_msgs
        limited_sec = app.config.get('BG_MONITOR_LAST_COMPLETED', {}).get(queue_name)
        if limited_sec is None:
            app.logger.warn(f'BG_MONITOR_LAST_COMPLETED for {queue_name=} not found ')

        err_msgs = []
        if limited_sec is not None and last_completed_date:
            limited_date = dates.before_now(limited_sec)
            if last_completed_date < limited_date:
                err_msgs.append(
                    f'last completed job is too old. [{last_completed_date} < {limited_date}]'
                )

        result_dict = dict(
            status=self.to_bg_status_str(
                not err_msgs and self.all_stable(itertools.chain(errors.values(), queued.values()))),
            last_completed_job=last_completed_date and dates.format(last_completed_date),
            errors=errors,
            queued=queued,
            err_msgs=err_msgs,
        )
        return result_dict

    def get_config_dict_by_queue_name(self, config_name, queue_name):
        bg_specs = background_helper.get_all_background_task_specs()
        actions = {action for qn, action, _ in bg_specs
                   if qn == queue_name}

        return {
            k: v
            for k, v in app.config.get(config_name, {}).items()
            if k in actions
        }

    def create_background_status(self) -> dict:
        queues = {
            queue_name: self.create_queues_status(queue_name)
            for queue_name in [BGJOB_QUEUE_TYPE_LONG, BGJOB_QUEUE_TYPE_MAIN]
        }

        result_dict = dict(
            status=(self.all_stable_str(queues.values())),
            queues=queues,
        )
        return result_dict

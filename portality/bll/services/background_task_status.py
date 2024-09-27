"""
~~BackgroundTask:Monitoring~~
"""
import itertools
from typing import Iterable

from constants import BGJOB_STATUS_COMPLETE
from portality.constants import BGJOB_QUEUE_ID_LONG, BGJOB_QUEUE_ID_MAIN, BGJOB_QUEUE_ID_EVENTS, BGJOB_QUEUE_ID_SCHEDULED_LONG, BGJOB_QUEUE_ID_SCHEDULED_SHORT, BGJOB_STATUS_ERROR, BGJOB_STATUS_QUEUED, \
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

    @staticmethod
    def is_stable(val):
        return val == BG_STATUS_STABLE

    @staticmethod
    def to_bg_status_str(stable_val: bool) -> str:
        return BG_STATUS_STABLE if stable_val else BG_STATUS_UNSTABLE

    def all_stable(self, items: Iterable, field_name='status') -> bool:
        return all(self.is_stable(q.get(field_name)) for q in items)

    def all_stable_str(self, items: Iterable, field_name='status') -> str:
        return self.to_bg_status_str(self.all_stable(items, field_name))

    def create_last_successfully_run_status(self, action, last_successful_run=0, **_) -> dict:
        if last_successful_run == 0:
            return dict(
                status=BG_STATUS_STABLE,
                last_run=None,
                last_run_status=None,
                err_msgs=[]
            )

        lr_query = (BackgroundJobQueryBuilder().action(action)
                    .since(dates.before_now(last_successful_run))
                    .size(1)
                    .order_by('created_date', 'desc')
                    .build_query_dict())

        lr_results = BackgroundJob.q2obj(q=lr_query)
        lr_job = lr_results and lr_results[0]

        status = BG_STATUS_UNSTABLE
        lr = None
        last_run_status = None
        msg = ["No background jobs run in the time period"]

        if lr_job is not None:
            lr = lr_job.created_date
            last_run_status = lr_job.status
            if lr_job.status == BGJOB_STATUS_COMPLETE:
                status = BG_STATUS_STABLE
                msg = []
            else:
                msg = ["Last job did not complete successfully"]

        return dict(
            status=status,
            last_run=lr,
            last_run_status=last_run_status,
            err_msgs=msg
        )



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
            err_msgs.append('outdated queued job found[{}]. created_timestamp[{} < {}]'.format(
                oldest_job.id,
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

        last_run = {action: self.create_last_successfully_run_status(action, **config) for action, config
                  in self.get_config_dict_by_queue_name('BG_MONITOR_LAST_SUCCESSFULLY_RUN_CONFIG', queue_name).items()}

        # prepare for err_msgs
        limited_sec = app.config.get('BG_MONITOR_LAST_COMPLETED', {}).get(queue_name)
        if limited_sec is None:
            app.logger.warning(f'BG_MONITOR_LAST_COMPLETED for {queue_name} not found ')

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
            last_successfully_run=last_run,
            err_msgs=err_msgs,
        )
        return result_dict

    @staticmethod
    def get_config_dict_by_queue_name(config_name, queue_name):
        bg_specs = background_helper.get_all_background_task_specs()
        actions = {action for qn, action, _ in bg_specs
                   if qn == queue_name}

        return {
            k: app.config.get(config_name, {}).get(k, app.config.get('BG_MONITOR_DEFAULT_CONFIG'))
            for k in actions
        }

    def create_background_status(self) -> dict:
        queues = {
            queue_name: self.create_queues_status(queue_name)
            for queue_name in [BGJOB_QUEUE_ID_LONG, BGJOB_QUEUE_ID_MAIN, BGJOB_QUEUE_ID_EVENTS, BGJOB_QUEUE_ID_SCHEDULED_LONG, BGJOB_QUEUE_ID_SCHEDULED_SHORT]
        }

        result_dict = dict(
            status=(self.all_stable_str(queues.values())),
            queues=queues,
        )

        # sort the results in the order of unstable status
        sorted_data = self.sort_dict_by_unstable_status(result_dict)

        return sorted_data

    def sort_dict_by_unstable_status(self, data):
        """
        Sorts each dictionary within the nested structure by prioritizing items with 'status': 'unstable'.
        The overall structure of the input dictionary is preserved.
        """
        if isinstance(data, dict):
            # Extract items with 'status': 'unstable' and other items
            unstable_items = {k: v for k, v in data.items() if isinstance(v, dict) and v.get('status') == 'unstable'}
            other_items = {k: v for k, v in data.items() if k not in unstable_items}

            # Recursively sort nested dictionaries
            for k in unstable_items:
                unstable_items[k] = self.sort_dict_by_unstable_status(unstable_items[k])
            for k in other_items:
                other_items[k] = self.sort_dict_by_unstable_status(other_items[k])

            # Merge the dictionaries, with unstable items first
            return {**unstable_items, **other_items}
        else:
            # Return the item as is if it's not a dict
            return data

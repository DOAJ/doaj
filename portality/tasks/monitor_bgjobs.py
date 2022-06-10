import itertools

from portality import app_email, models
from portality.background import BackgroundTask
from portality.core import app
from portality.decorators import write_required
from portality.tasks.helpers import background_helper
from portality.tasks.redis_huey import schedule, long_running


def get_system_email():
    return app.config.get('SYSTEM_EMAIL_FROM', 'helpdesk@doaj.org')


def send_mail_if_bgjob_error(to_address_list, from_address, logger_fn=None):
    if logger_fn is None:
        logger_fn = print

    raw_query = {
        'query': {'bool': {'must': [
            {'term': {'status.exact': 'error'}},
            {'term': {'user.exact': 'system'}},
            {'term': {'action.exact': 'harvest'}},
        ]
        }},
        'sort': [{'created_date': {'order': 'desc'}}],
        'track_total_hits': True}

    jobs = models.BackgroundJob.q2obj(q=raw_query)
    logger_fn(f'[monitor_bgjobs] {len(jobs)} of background jobs found.')

    def _to_msg_lines(_jobs):
        return [
            '--------------',
            f'{_jobs.action} by {_jobs.user} status: {_jobs.status}',
            f'Job ID: {_jobs.id}',
            f'Job Created: {_jobs.created_date}',
            f'Job Last Updated: {_jobs.last_updated}',
        ]

    msg_lines = itertools.chain.from_iterable(_to_msg_lines(j) for j in jobs)
    msg_body = f'{len(jobs)} of background jobs found.\n'
    msg_body += '\n'.join(msg_lines)
    app_email.send_mail(to_address_list, from_address,
                        '[Monitoring Background job] error background jobs found.',
                        msg_body=msg_body)


class MonitorBgjobsBackgroundTask(BackgroundTask):
    __action__ = "monitor_bgjobs"

    def run(self):
        kwargs = {k: self.get_param(self.background_job.params, k)
                  for k in ['to_address_list', 'from_address']}
        kwargs['logger_fn'] = self.background_job.add_audit_message
        send_mail_if_bgjob_error(**kwargs)
        self.background_job.add_audit_message(f"{self.__action__} completed")

    @classmethod
    def prepare(cls, username, **kwargs):
        params = {}
        cls.set_param(params, 'to_address_list', background_helper.get_value_safe(
            'to_address_list', [get_system_email(), ], kwargs))
        cls.set_param(params, 'from_address', background_helper.get_value_safe(
            'from_address', get_system_email(), kwargs))
        return background_helper.create_job(username=username,
                                            action=cls.__action__,
                                            params=params)

    def cleanup(self):
        pass

    @classmethod
    def submit(cls, background_job):
        background_helper.submit_by_background_job(background_job, execute_monitor_bgjobs)


@long_running.periodic_task(schedule(MonitorBgjobsBackgroundTask.__action__))
@write_required(script=True)
def scheduled_monitor_bgjobs():
    background_helper.submit_by_bg_task_type(
        MonitorBgjobsBackgroundTask,
        to_address_list=app.config.get("TASKS_MONITOR_BGJOBS_TO", [get_system_email(), ]),
        from_address=app.config.get("TASKS_MONITOR_BGJOBS_FROM", get_system_email()),
    )


execute_monitor_bgjobs = background_helper.create_execute_fn(long_running, MonitorBgjobsBackgroundTask)

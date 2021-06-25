from portality import models
from portality.background import BackgroundTask, BackgroundApi

from portality.tasks.harvester_helpers import workflow
from portality.core import app
from portality.models.harvester import HarvesterProgressReport as Report
from portality.tasks.redis_huey import schedule, long_running
from portality.decorators import write_required

import datetime

class HarvesterBackgroundTask(BackgroundTask):
    mail_prereqs = False
    __action__ = "harvest"

    def run(self):
        """
        Execute the task as specified by the background_job
        :return:
        """
        accs = list(app.config.get("HARVESTER_API_KEYS", {}).keys())
        harvester_workflow = workflow.HarvesterWorkflow()
        for account_id in accs:
            harvester_workflow.process_account(account_id)
            self.background_job.add_audit_message(harvester_workflow.logger)

        report = Report.write_report()
        app.logger.info(report)

        # If the harvester finishes normally, we can email the report.
        if self.mail_prereqs:
            self.mail.send_mail(
                to=app.config["HARVESTER_EMAIL_RECIPIENTS"],
                fro=self.fro,
                subject=self.sub_prefix + "DOAJ Harvester finished at {0}".format(
                    datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")),
                msg_body=report
            )

            return

    def cleanup(self):
        """
        Cleanup after a successful OR failed run of the task
        :return:
        """
        pass

    @classmethod
    def prepare(cls, username, **kwargs):
        """
        Take an arbitrary set of keyword arguments and return an instance of a BackgroundJob,
        or fail with a suitable exception

        :param kwargs: arbitrary keyword arguments pertaining to this task type
        :return: a BackgroundJob instance representing this task
        """

        # run_only_once()
        # initialise_index(app, es_connection)
        cls.sub_prefix = app.config.get('HARVESTER_EMAIL_SUBJECT_PREFIX', '')

        # Send an email when the harvester starts.
        cls.mail_prereqs = False
        cls.fro = app.config.get("HARVESTER_EMAIL_FROM_ADDRESS", 'harvester@doaj.org')
        if app.config.get("HARVESTER_EMAIL_ON_EVENT", False):
            to = app.config.get("HARVESTER_EMAIL_RECIPIENTS", None)

            if to is not None:
                cls.mail_prereqs = True
                from portality import app_email as mail
                mail.send_mail(
                    to=to,
                    fro=cls.fro,
                    subject=cls.sub_prefix + "DOAJ Harvester started at {0}".format(
                        datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")),
                    msg_body="A new running instance of the harvester has started."
                )

        # first prepare a job record
        job = models.BackgroundJob()
        job.user = username
        job.action = cls.__action__
        return job

    @classmethod
    def submit(cls, background_job):
        """
        Submit the specified BackgroundJob to the background queue

        :param background_job: the BackgroundJob instance
        :return:
        """
        background_job.save()
        harvest.schedule(args=(background_job.id,), delay=10)
        # fixme: schedule() could raise a huey.exceptions.HueyException and not reach redis- would that be logged?


@long_running.periodic_task(schedule("harvest"))
@write_required(script=True)
def scheduled_harvest():
    user = app.config.get("SYSTEM_USERNAME")
    job = HarvesterBackgroundTask.prepare(user)
    HarvesterBackgroundTask.submit(job)

@long_running.task()
@write_required(script=True)
def harvest(job_id):
    job = models.BackgroundJob.pull(job_id)
    task = HarvesterBackgroundTask(job)
    BackgroundApi.execute(task)

from portality import models
from portality.background import BackgroundTask, BackgroundApi

from portality.harvester import workflow
from portality.core import app, es_connection, initialise_index
from portality.models.harvester import HarvesterProgressReport as Report
import flask.logging

from setproctitle import setproctitle
import psutil, time, datetime

STARTING_PROCTITLE = app.config.get('HARVESTER_STARTING_PROCTITLE', 'harvester: starting')
RUNNING_PROCTITLE = app.config.get('HARVESTER_RUNNING_PROCTITLE', 'harvester: running')
MAX_WAIT = app.config.get('HARVESTER_MAX_WAIT', 10)

class HarvesterBackgroundTask(BackgroundTask):
    mail_prereqs = False
    __action__ = "harvest"

    def run(self):
        """
        Execute the task as specified by the background_job
        :return:
        """
        accs = list(app.config.get("HARVESTER_API_KEYS", {}).keys())
        for account_id in accs:
            workflow.HarvesterWorkflow.process_account(account_id)

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

        if app.debug:
            # Augment the default flask debug log to include a timestamp.
            app.debug_log_format = (
                    '-' * 80 + '\n' +
                    '%(asctime)s\n'
                    '%(levelname)s in %(module)s [%(pathname)s:%(lineno)d]:\n' +
                    '%(message)s\n' +
                    '-' * 80
            )
            flask.logging.create_logger(app)

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
        # read_news.schedule(args=(background_job.id,), delay=10)
        # fixme: schedule() could raise a huey.exceptions.HueyException and not reach redis- would that be logged?

def run_only_once():
    # Identify running harvester instances.
    setproctitle(STARTING_PROCTITLE)
    running_harvesters = []
    starting_harvesters = []
    for p in psutil.process_iter():
        try:
            if p.cmdline() and p.cmdline()[0] == RUNNING_PROCTITLE:
                running_harvesters.append(p)
            if p.cmdline() and p.cmdline()[0] == STARTING_PROCTITLE:
                starting_harvesters.append(p)
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            pass

    if len(starting_harvesters) > 1:
        print("Harvester is already starting. Aborting this instance.")
        exit(1)

    # Send SIGTERM to all extant instances of the harvester.
    if len(running_harvesters) > 0:
        print("Sending SIGTERM to extant harvester instances.")
        [h.terminate() for h in running_harvesters]

    # Check if they terminated correctly
    started = datetime.datetime.utcnow()
    still_running = [hrv for hrv in running_harvesters if hrv.is_running()]
    while len(still_running) > 0 and datetime.datetime.utcnow() - started < datetime.timedelta(minutes=MAX_WAIT):
        time.sleep(10)
        still_running = [hrv for hrv in running_harvesters if hrv.is_running()]

    # Move on to killing the processes if they don't respond to terminate
    if len(still_running) > 0:
        print("Old Harvesters are still running. Escalating to SIGKILL.")
        [h.kill() for h in running_harvesters]
        time.sleep(10)

    # Startup complete, change process name to running.
    setproctitle(RUNNING_PROCTITLE)

# @main_queue.periodic_task(schedule("harvest"))
# @write_required(script=True)
# def scheduled_read_news():
#     user = app.config.get("SYSTEM_USERNAME")
#     job = HarvesterBackgroundTask.prepare(user)
#     HarvesterBackgroundTask.submit(job)
#
#
# @main_queue.task()
# @write_required(script=True)
# def harvest(job_id):
#     job = models.BackgroundJob.pull(job_id)
#     task = HarvesterBackgroundTask(job)
#     BackgroundApi.execute(task)

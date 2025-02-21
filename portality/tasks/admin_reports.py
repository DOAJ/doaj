from portality import models
from portality.background import BackgroundTask, BackgroundApi
from portality.bll.doaj import DOAJ
from portality.core import app
from portality.tasks.helpers import background_helper
from portality.tasks.redis_huey import events_queue as queue
from portality import constants
from portality.util import url_for

import json


class AdminReportsBackgroundTask(BackgroundTask):

    __action__ = "admin_reports"

    MODELS = {
        "journal": models.Journal,
        "application": models.Application
    }

    def __init__(self, background_job):
        super(AdminReportsBackgroundTask, self).__init__(background_job)
        self.filename = None

    def run(self):
        """
        Execute the task as specified by the background_job 
        :return:
        """
        job = self.background_job

        params = job.params
        model_type = self.get_param(params, "model", "journal")
        query_raw = self.get_param(params, "query", None)
        ui_query_raw = self.get_param(params, "ui_query", None)
        name = self.get_param(params, "name", None)

        model = self.MODELS.get(model_type, models.Journal)
        query = json.loads(query_raw) if query_raw is not None else None

        # generate the admin csv in the temp store
        export_svc = DOAJ.exportService()
        filepath, filename = export_svc.csv(model, query,
                                              admin_fieldset=True,
                                              obscure_accounts=False,
                                              add_sensitive_account_info=True,
                                              exclude_no_issn=False
                                              )
        self.filename = filename

        # publish it to the main store and record its existence
        export = export_svc.publish(filepath, filename, requester=job.user, request_date=job.created_date, name=name, query=ui_query_raw, model=model)
        job.add_audit_message("Export generated with id {id}".format(id=export.id))

        # send a notification to the requesting user
        notify_svc = DOAJ.notificationsService()

        # note we're using the doaj url_for wrapper, not the flask url_for directly, due to the request context hack required
        url = url_for("admin.get_report", report_id=export.id)

        source_id = "bg:job:" + self.__action__ + ":export_available"

        notification = models.Notification()
        notification.who = job.user
        notification.created_by = source_id
        notification.classification = constants.NOTIFICATION_CLASSIFICATION_FINISHED
        notification.long = notify_svc.long_notification(source_id).format(name=name)
        notification.short = notify_svc.short_notification(source_id)
        notification.action = url
        notify_svc.notify(notification)

    def cleanup(self):
        """
        Cleanup after a successful OR failed run of the task
        :return:
        """
        if self.filename is not None:
            export_svc = DOAJ.exportService()
            export_svc.delete_tmp_csv(self.filename)
            self.filename = None

    @classmethod
    def prepare(cls, username, **kwargs):
        """
        Take an arbitrary set of keyword arguments and return an instance of a BackgroundJob,
        or fail with a suitable exception

        :param kwargs: arbitrary keyword arguments pertaining to this task type
        :return: a BackgroundJob instance representing this task
        """
        # prepare a job record
        model = kwargs.get("model", "journal")
        query = kwargs.get("true_query", None)
        ui_query = kwargs.get("ui_query", None)
        name = kwargs.get("name", None)

        params = {}
        cls.set_param(params, "model", model)
        cls.set_param(params, "query", json.dumps(query))
        cls.set_param(params, "ui_query", json.dumps(ui_query))
        cls.set_param(params, "name", name)

        # first prepare a job record
        job = background_helper.create_job(username=username,
                                           action=cls.__action__,
                                           params=params,
                                           queue_id=huey_helper.queue_id, )

        return job

    @classmethod
    def submit(cls, background_job):
        """
        Submit the specified BackgroundJob to the background queue

        :param background_job: the BackgroundJob instance
        :return:
        """
        background_job.save()
        admin_reports.schedule(args=(background_job.id,), delay=app.config.get('HUEY_ASYNC_DELAY', 10))


huey_helper = AdminReportsBackgroundTask.create_huey_helper(queue)


@huey_helper.register_execute(is_load_config=False)
def admin_reports(job_id):
    job = models.BackgroundJob.pull(job_id)
    task = AdminReportsBackgroundTask(job)
    BackgroundApi.execute(task)

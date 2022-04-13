from flask import url_for

from portality.events.consumer import EventConsumer
from portality import constants
from portality import models
from portality.lib import edges
from portality.bll import DOAJ
from portality.bll import exceptions
from portality.dao import Facetview2


class BGJobFinishedNotify(EventConsumer):
    ID = "bg:job_finished:notify"

    @classmethod
    def consumes(cls, event):
        return event.id == constants.BACKGROUND_JOB_FINISHED and \
               event.context.get("job") is not None

    @classmethod
    def consume(cls, event):
        context = event.context
        job_id = context.get("job")
        if job_id is None:
            return
        job = models.BackgroundJob.pull(job_id)
        if job is None:
            raise exceptions.NoSuchObjectException("No background job with id {x} found".format(x=job_id))
        if job.user is None:
            return

        acc = models.Account.pull(job.user)
        if acc is None or not acc.has_role("admin"):
            return

        svc = DOAJ.notificationsService()

        query = Facetview2.make_query(job.id)
        url = "admin/background_jobs?source=" + Facetview2.url_encode_query(query)

        notification = models.Notification()
        notification.who = acc.id
        notification.created_by = cls.ID
        notification.classification = constants.NOTIFICATION_CLASSIFICATION_FINISHED
        notification.message = svc.message(cls.ID).format(job_id=job.id, action=job.action, status=job.status)
        notification.action = url

        svc.notify(notification)

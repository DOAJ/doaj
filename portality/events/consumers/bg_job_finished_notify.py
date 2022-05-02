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
        source = event.context.get("job")
        try:
            job = models.BackgroundJob(**source)
        except Exception as e:
            raise exceptions.NoSuchObjectException("Unable to construct a BackgroundJob object from the data supplied {x}".format(x=e))

        if job.user is None:
            return

        acc = models.Account.pull(job.user)
        if acc is None or not acc.has_role("admin"):
            return

        svc = DOAJ.notificationsService()

        string_id_query = edges.make_url_query(query_string=job.id)
        url = url_for("admin.background_jobs_search", source=string_id_query)

        notification = models.Notification()
        notification.who = acc.id
        notification.created_by = cls.ID
        notification.classification = constants.NOTIFICATION_CLASSIFICATION_FINISHED
        notification.message = svc.message(cls.ID).format(job_id=job.id, action=job.action, status=job.status)
        notification.action = url

        svc.notify(notification)

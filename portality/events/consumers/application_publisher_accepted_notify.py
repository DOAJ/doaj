from flask import url_for
from datetime import datetime

from portality.events.consumer import EventConsumer
from portality import constants
from portality import models
from portality.lib import edges
from portality.bll import DOAJ, exceptions


class ApplicationPublisherAcceptedNotify(EventConsumer):
    ID = "application:publisher:accepted:notify"

    @classmethod
    def consumes(cls, event):
        return event.id == constants.EVENT_APPLICATION_STATUS and \
                event.context.get("application") is not None and \
                event.context.get("old_status") != constants.APPLICATION_STATUS_ACCEPTED and \
                event.context.get("new_status") == constants.APPLICATION_STATUS_ACCEPTED

    @classmethod
    def consume(cls, event):
        app_source = event.context.get("application")

        try:
            application = models.Application(**app_source)
        except Exception as e:
            raise exceptions.NoSuchObjectException("Unable to construct Application from supplied source - data structure validation error, {x}".format(x=e))

        if not application.owner:
            return


        svc = DOAJ.notificationsService()

        notification = models.Notification()
        notification.who = application.owner
        notification.created_by = cls.ID
        notification.classification = constants.NOTIFICATION_CLASSIFICATION_STATUS_CHANGE
        datetime_object = datetime.strptime(application.date_applied, '%Y-%m-%dT%H:%M:%SZ')
        date_applied = datetime_object.strftime("%d/%b/%Y")
        string_id_query = edges.make_url_query(query_string=application.id)
        url_for_journal = url_for("publisher.journals", source=string_id_query)
        url_faq=url_for("doaj.faq")
        notification.message = svc.message(cls.ID).format(
            title=application.bibjson().title,
            date_applied=date_applied,
            url_for_journal=url_for_journal,
            url_faq=url_faq
        )
        svc.notify(notification)

from portality.core import app
from portality.lib import plugin

from portality.events.consumers.account_created_email import AccountCreatedEmail
from portality.events.consumers.application_assed_inprogress_notify import ApplicationAssedInprogressNotify
from portality.events.consumers.application_assed_assigned_notify import ApplicationAssedAssignedNotify
from portality.events.consumers.bg_job_finished_notify import BGJobFinishedNotify
from portality.events.consumers.application_maned_ready_notify import ApplicationManedReadyNotify
from portality.events.consumers.application_publisher_created_notify import ApplicationPublisherCreatedNotify
from portality.events.consumers.application_publisher_revision_notify import ApplicationPublisherRevisionNotify
from portality.events.consumers.application_editor_completed_notify import ApplicationEditorCompletedNotify
from portality.events.consumers.application_editor_inprogress_notify import ApplicationEditorInProgressNotify
from portality.events.consumers.account_passwordreset_email import AccountPasswordResetEmail
from portality.events.consumers.application_editor_group_assigned_notify import ApplicationEditorGroupAssignedNotify
from portality.events.consumers.application_publisher_quickreject_notify import ApplicationPublisherQuickRejectNotify
from portality.events.consumers.application_publisher_accepted_notify import ApplicationPublisherAcceptedNotify
from portality.events.consumers.update_request_publisher_accepted_notify import UpdateRequestPublisherAcceptedNotify
from portality.events.consumers.application_publisher_assigned_notify import ApplicationPublisherAssignedNotify
from portality.events.consumers.update_request_publisher_assigned_notify import UpdateRequestPublisherAssignedNotify
from portality.events.consumers.journal_assed_assigned_notify import JournalAssedAssignedNotify
from portality.events.consumers.journal_editor_group_assigned_notify import JournalEditorGroupAssignedNotify
from portality.events.consumers.application_publisher_inprogress_notify import ApplicationPublisherInprogressNotify
from portality.events.consumers.update_request_publisher_rejected_notify import UpdateRequestPublisherRejectedNotify


class EventsService(object):
    EVENT_CONSUMERS = [
        ApplicationPublisherQuickRejectNotify,
        AccountCreatedEmail,
        AccountPasswordResetEmail,
        ApplicationAssedInprogressNotify,
        ApplicationAssedAssignedNotify,
        ApplicationEditorCompletedNotify,
        ApplicationEditorInProgressNotify,
        ApplicationEditorGroupAssignedNotify,
        ApplicationManedReadyNotify,
        ApplicationPublisherCreatedNotify,
        ApplicationPublisherInprogressNotify,
        ApplicationPublisherAcceptedNotify,
        ApplicationPublisherAssignedNotify,
        ApplicationPublisherRevisionNotify,
        BGJobFinishedNotify,
        JournalAssedAssignedNotify,
        JournalEditorGroupAssignedNotify,
        UpdateRequestPublisherAcceptedNotify,
        UpdateRequestPublisherAssignedNotify,
        UpdateRequestPublisherRejectedNotify
    ]

    def __init__(self):
        self.trigger_function = plugin.load_function(app.config.get("EVENT_SEND_FUNCTION"))

    def trigger(self, event):
        self.trigger_function(event)

    def consume(self, event):
        for consumer in self.EVENT_CONSUMERS:
            try:
                if consumer.consumes(event):
                    consumer.consume(event)
            except Exception as e:
                app.logger.error("Error in consumer {x}: {e}".format(e=str(e), x=consumer.ID))

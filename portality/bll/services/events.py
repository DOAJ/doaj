from portality.core import app
from portality.events.consumers.update_request_publisher_submitted_notify import UpdateRequestPublisherSubmittedNotify
from portality.lib import plugin

from portality.events.consumers.account_created_email import AccountCreatedEmail
from portality.events.consumers.application_assed_inprogress_notify import ApplicationAssedInprogressNotify
from portality.events.consumers.application_assed_assigned_notify import ApplicationAssedAssignedNotify
from portality.events.consumers.application_assed_acceptreject_notify import ApplicationAssedAcceptRejectNotify
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
from portality.events.consumers.journal_discontinuing_soon_notify import JournalDiscontinuingSoonNotify
from portality.events.consumers.application_editor_acceptreject_notify import ApplicationEditorAcceptRejectNotify
from portality.events.consumers.update_request_maned_editor_group_assigned_notify import UpdateRequestManedEditorGroupAssignedNotify



class EventsService(object):
    # disabled events - to enable move the event to EVENT_CONSUMERS array
    DISABLED_EVENTS = [
        ApplicationPublisherAssignedNotify, # https://github.com/DOAJ/doajPM/issues/3974
        ApplicationPublisherInprogressNotify, # https://github.com/DOAJ/doajPM/issues/3974
        ApplicationPublisherRevisionNotify,
        JournalEditorGroupAssignedNotify, # https://github.com/DOAJ/doajPM/issues/3974
        JournalAssedAssignedNotify, # https://github.com/DOAJ/doajPM/issues/3974
        UpdateRequestPublisherAssignedNotify, # https://github.com/DOAJ/doajPM/issues/3974
    ]
    EVENT_CONSUMERS = [
        AccountCreatedEmail,
        AccountPasswordResetEmail,
        ApplicationAssedAcceptRejectNotify,
        ApplicationAssedAssignedNotify,
        ApplicationAssedInprogressNotify,
        ApplicationEditorAcceptRejectNotify,
        ApplicationEditorCompletedNotify,
        ApplicationEditorGroupAssignedNotify,
        ApplicationEditorInProgressNotify,
        ApplicationManedReadyNotify,
        ApplicationPublisherAcceptedNotify,
        ApplicationPublisherCreatedNotify,
        ApplicationPublisherQuickRejectNotify,
        BGJobFinishedNotify,
        JournalDiscontinuingSoonNotify,
        UpdateRequestManedEditorGroupAssignedNotify,
        UpdateRequestPublisherAcceptedNotify,
        UpdateRequestPublisherRejectedNotify,
        UpdateRequestPublisherSubmittedNotify
    ]

    def __init__(self):
        self.trigger_function = plugin.load_function(app.config.get("EVENT_SEND_FUNCTION"))

    def trigger(self, event):
        self.trigger_function(event)

    def consume(self, event):
        for consumer in self.EVENT_CONSUMERS:
            try:
                if consumer.should_consume(event):
                    consumer.consume(event)
            except Exception as e:
                app.logger.error("Error in consumer {x}: {e}".format(e=str(e), x=consumer.ID))

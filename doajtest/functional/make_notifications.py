# ~~Notifications:FunctionalTest~~
import models
from portality.events.consumers import application_assed_assigned_notify, \
    application_assed_inprogress_notify, \
    application_editor_completed_notify, \
    application_editor_group_assigned_notify, \
    application_editor_inprogress_notify, \
    application_maned_ready_notify, \
    application_publisher_accepted_notify, \
    application_publisher_assigned_notify, \
    application_publisher_created_notify, \
    application_publisher_inprogress_notify, \
    application_publisher_quickreject_notify, \
    application_publisher_revision_notify, \
    bg_job_finished_notify, \
    journal_assed_assigned_notify, \
    journal_editor_group_assigned_notify, \
    update_request_publisher_accepted_notify, \
    update_request_publisher_assigned_notify, \
    update_request_publisher_rejected_notify
from portality.models.event import Event
from portality.models import EditorGroup
from doajtest.fixtures.v2.applications import ApplicationFixtureFactory
from doajtest.fixtures.v2.journals import JournalFixtureFactory
from portality import constants

USER = "richard"

NOTIFICATIONS = [
    "application_assed_assigned_notify",
    "application_assed_inprogress_notify",
    "application_editor_completed_notify",
    "application_editor_group_assigned_notify",
    "application_editor_inprogress_notify",
    "application_maned_ready_notify",
    "application_publisher_accepted_notify",
    "application_publisher_assigned_notify",
    "application_publisher_created_notify",
    "application_publisher_inprogress_notify",
    "application_publisher_quickreject_notify",
    "application_publisher_revision_notify",
    "bg_job_finished_notify",
    "journal_assed_assigned_notify",
    "journal_editor_group_assigned_notify",
    "update_request_publisher_accepted_notify",
    "update_request_publisher_assigned_notify",
    "update_request_publisher_rejected_notify"
]


##############################################
## ApplicationAssedAssignedNotify
if "application_assed_assigned_notify" in NOTIFICATIONS:
    aaan_application = ApplicationFixtureFactory.make_application_source()
    aaan_application["admin"]["editor"] = USER
    aaan_application["bibjson"]["title"] = "Application Assed Assigned Notify"
    aaan_application["id"] = "application_assed_assigned_notify"

    event = Event(constants.EVENT_APPLICATION_ASSED_ASSIGNED, context={
        "application": aaan_application
    })
    aaan = application_assed_assigned_notify.ApplicationAssedAssignedNotify()
    aaan.consume(event)


##############################################
## ApplicationAssedAssignedNotify
if "application_assed_inprogress_notify" in NOTIFICATIONS:
    aain_application = ApplicationFixtureFactory.make_application_source()
    aain_application["admin"]["editor"] = USER
    aain_application["bibjson"]["title"] = "Application Assed In Progress Notify"
    aain_application["id"] = "application_assed_inprogress_notify"

    event = Event(constants.EVENT_APPLICATION_STATUS, context={
        "application": aain_application
    })
    aain = application_assed_inprogress_notify.ApplicationAssedInprogressNotify()
    aain.consume(event)


##############################################
## ApplicationEditorCompletedNotify
if "application_editor_completed_notify" in NOTIFICATIONS:
    def editor_group_mock_pull(editor_group_id):
        return EditorGroup(**{
            "editor": USER
        })

    eg_pull = EditorGroup.pull
    EditorGroup.pull = editor_group_mock_pull

    aecn_application = ApplicationFixtureFactory.make_application_source()
    aecn_application["bibjson"]["title"] = "Application Editor Completed Notify"
    aecn_application["id"] = "application_editor_completed_notify"

    event = Event(constants.EVENT_APPLICATION_STATUS, context={
        "application": aecn_application
    })
    aecn = application_editor_completed_notify.ApplicationEditorCompletedNotify()
    aecn.consume(event)

    EditorGroup.pull = eg_pull

##############################################
## ApplicationEditorGroupAssignedNotify
if "application_editor_group_assigned_notify" in NOTIFICATIONS:
    def editor_group_mock_pull(key, value):
        return EditorGroup(**{
            "editor": USER
        })

    eg_pull = EditorGroup.pull_by_key
    EditorGroup.pull_by_key = editor_group_mock_pull

    aegan_application = ApplicationFixtureFactory.make_application_source()
    aegan_application["bibjson"]["title"] = "Application Editor Group Assigned Notify"
    aegan_application["id"] = "application_editor_group_assigned_notify"

    event = Event(constants.EVENT_APPLICATION_EDITOR_GROUP_ASSIGNED, context={
        "application": aegan_application
    })
    aegan = application_editor_group_assigned_notify.ApplicationEditorGroupAssignedNotify()
    aegan.consume(event)

    EditorGroup.pull_by_key = eg_pull


##############################################
## ApplicationEditorInprogressNotify
if "application_editor_inprogress_notify" in NOTIFICATIONS:
    def editor_group_mock_pull(editor_group_id):
        return EditorGroup(**{
            "editor": USER
        })

    eg_pull = EditorGroup.pull
    EditorGroup.pull = editor_group_mock_pull

    aein_application = ApplicationFixtureFactory.make_application_source()
    aein_application["bibjson"]["title"] = "Application Editor In Progress Notify"
    aein_application["id"] = "application_editor_inprogress_notify"

    event = Event(constants.EVENT_APPLICATION_STATUS, context={
        "application": aein_application
    })
    aein = application_editor_inprogress_notify.ApplicationEditorInProgressNotify()
    aein.consume(event)

    EditorGroup.pull = eg_pull


##############################################
## ApplicationManedReadyNotify
if "application_maned_ready_notify" in NOTIFICATIONS:
    def editor_group_mock_pull(key, value):
        return EditorGroup(**{
            "maned": USER
        })

    eg_pull = EditorGroup.pull_by_key
    EditorGroup.pull_by_key = editor_group_mock_pull

    application = ApplicationFixtureFactory.make_application_source()
    application["bibjson"]["title"] = "Application Maned Ready Notify"
    application["id"] = "application_maned_ready_notify"

    event = Event(constants.EVENT_APPLICATION_STATUS, context={
        "application": application
    })
    con = application_maned_ready_notify.ApplicationManedReadyNotify()
    con.consume(event)

    EditorGroup.pull_by_key = eg_pull

##############################################
## ApplicationPublisherAcceptedNotify
if "application_publisher_accepted_notify" in NOTIFICATIONS:
    application = ApplicationFixtureFactory.make_application_source()
    application["admin"]["owner"] = USER
    application["bibjson"]["title"] = "Application Publisher Accepted Notify"
    application["id"] = "application_publisher_accepted_notify"

    event = Event(constants.EVENT_APPLICATION_STATUS, context={
        "application": application
    })
    con = application_publisher_accepted_notify.ApplicationPublisherAcceptedNotify()
    con.consume(event)

##############################################
## ApplicationPublisherAssignedNotify
if "application_publisher_assigned_notify" in NOTIFICATIONS:
    application = ApplicationFixtureFactory.make_application_source()
    application["admin"]["owner"] = USER
    application["bibjson"]["title"] = "Application Publisher Assigned Notify"
    application["id"] = "application_publisher_assigned_notify"

    event = Event(constants.EVENT_APPLICATION_ASSED_ASSIGNED, context={
        "application": application
    })
    con = application_publisher_assigned_notify.ApplicationPublisherAssignedNotify()
    con.consume(event)


##############################################
## ApplicationPublisherCreatedNotify
if "application_publisher_created_notify" in NOTIFICATIONS:
    application = ApplicationFixtureFactory.make_application_source()
    application["admin"]["owner"] = USER
    application["bibjson"]["title"] = "Application Publisher Created Notify"
    application["id"] = "application_publisher_created_notify"

    event = Event(constants.EVENT_APPLICATION_CREATED, context={
        "application": application
    })
    con = application_publisher_created_notify.ApplicationPublisherCreatedNotify()
    con.consume(event)

##############################################
## ApplicationPublisherInprogressNotify
if "application_publisher_inprogress_notify" in NOTIFICATIONS:
    application = ApplicationFixtureFactory.make_application_source()
    application["admin"]["owner"] = USER
    application["bibjson"]["title"] = "Application Publisher In Progress Notify"
    application["id"] = "application_publisher_inprogress_notify"

    event = Event(constants.EVENT_APPLICATION_STATUS, context={
        "application": application
    })
    con = application_publisher_inprogress_notify.ApplicationPublisherInprogressNotify()
    con.consume(event)

##############################################
## ApplicationPublisherQuickRejectNotify
if "application_publisher_quickreject_notify" in NOTIFICATIONS:
    application = ApplicationFixtureFactory.make_application_source()
    application["admin"]["owner"] = USER
    application["bibjson"]["title"] = "Application Publisher Quick Reject Notify"
    application["id"] = "application_publisher_quickreject_notify"

    event = Event(constants.EVENT_APPLICATION_STATUS, context={
        "application": application
    })
    con = application_publisher_quickreject_notify.ApplicationPublisherQuickRejectNotify()
    con.consume(event)

##############################################
## ApplicationPublisherQuickRejectNotify
if "application_publisher_revision_notify" in NOTIFICATIONS:
    application = ApplicationFixtureFactory.make_application_source()
    application["admin"]["owner"] = USER
    application["bibjson"]["title"] = "Application Publisher Revision Notify"
    application["id"] = "application_publisher_revision_notify"

    event = Event(constants.EVENT_APPLICATION_STATUS, context={
        "application": application
    })
    con = application_publisher_revision_notify.ApplicationPublisherRevisionNotify()
    con.consume(event)

##############################################
## BGJobFinishedNotify
if "bg_job_finished_notify" in NOTIFICATIONS:
    job = models.BackgroundJob(**{
        "id": "bg_job_finished_notify",
        "user": USER,
        "action": "bg_job_finished_notify",
        "status": "complete"
    })

    event = Event(constants.BACKGROUND_JOB_FINISHED, context={
        "job": job
    })
    con = bg_job_finished_notify.BGJobFinishedNotify()
    con.consume(event)

##############################################
## JournalAssedAssignedNotify
if "journal_assed_assigned_notify" in NOTIFICATIONS:
    journal = JournalFixtureFactory.make_journal_source(in_doaj=True)
    journal["admin"]["editor"] = USER
    journal["bibjson"]["title"] = "Journal Assed Assigned Notify"
    journal["id"] = "journal_assed_assigned_notify"

    event = Event(constants.EVENT_JOURNAL_ASSED_ASSIGNED, context={
        "journal": journal
    })
    con = journal_assed_assigned_notify.JournalAssedAssignedNotify()
    con.consume(event)

##############################################
## JournalEditorGroupAssignedNotify
if "journal_editor_group_assigned_notify" in NOTIFICATIONS:
    def editor_group_mock_pull(key, value):
        return EditorGroup(**{
            "editor": USER
        })

    eg_pull = EditorGroup.pull_by_key
    EditorGroup.pull_by_key = editor_group_mock_pull

    journal = JournalFixtureFactory.make_journal_source(in_doaj=True)
    journal["admin"]["editor"] = USER
    journal["bibjson"]["title"] = "Journal Editor Group Assigned Notify"
    journal["id"] = "journal_editor_group_assigned_notify"

    event = Event(constants.EVENT_APPLICATION_EDITOR_GROUP_ASSIGNED, context={
        "journal": journal
    })
    aegan = journal_editor_group_assigned_notify.JournalEditorGroupAssignedNotify()
    aegan.consume(event)

    EditorGroup.pull_by_key = eg_pull

##############################################
## UpdateRequestPublisherAcceptedNotify
if "update_request_publisher_accepted_notify" in NOTIFICATIONS:
    application = ApplicationFixtureFactory.make_application_source()
    application["admin"]["owner"] = USER
    application["bibjson"]["title"] = "Update Request Publisher Accepted Notify"
    application["id"] = "update_request_publisher_accepted_notify"

    event = Event(constants.EVENT_APPLICATION_STATUS, context={
        "application": application
    })
    con = update_request_publisher_accepted_notify.UpdateRequestPublisherAcceptedNotify()
    con.consume(event)

##############################################
## UpdateRequestPublisherAssignedNotify
if "update_request_publisher_assigned_notify" in NOTIFICATIONS:
    application = ApplicationFixtureFactory.make_application_source()
    application["admin"]["owner"] = USER
    application["bibjson"]["title"] = "Update Request Publisher Assigned Notify"
    application["id"] = "update_request_publisher_assigned_notify"

    event = Event(constants.EVENT_APPLICATION_ASSED_ASSIGNED, context={
        "application": application
    })
    con = update_request_publisher_assigned_notify.UpdateRequestPublisherAssignedNotify()
    con.consume(event)

##############################################
## UpdateRequestPublisherRejectedNotify
if "update_request_publisher_rejected_notify" in NOTIFICATIONS:
    application = ApplicationFixtureFactory.make_application_source()
    application["admin"]["owner"] = USER
    application["bibjson"]["title"] = "Update Request Publisher Rejected Notify"
    application["id"] = "update_request_publisher_rejected_notify"

    event = Event(constants.EVENT_APPLICATION_STATUS, context={
        "application": application
    })
    con = update_request_publisher_rejected_notify.UpdateRequestPublisherRejectedNotify()
    con.consume(event)
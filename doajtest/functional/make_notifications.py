from portality.events.consumers import application_assed_assigned_notify, \
    application_assed_inprogress_notify, \
    application_editor_completed_notify, \
    application_editor_group_assigned_notify, \
    application_editor_inprogress_notify
from portality.models.event import Event
from portality.models import EditorGroup
from doajtest.fixtures.v2.applications import ApplicationFixtureFactory
from portality import constants

USER = "richard"

NOTIFICATIONS = [
    # "application_assed_assigned_notify",
    # "application_assed_inprogress_notify",
    # "application_editor_completed_notify",
    # "application_editor_group_assigned_notify",
    # "application_editor_inprogress_notify",
    "application_maned_ready_notify"
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
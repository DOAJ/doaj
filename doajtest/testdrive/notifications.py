from doajtest.fixtures import ApplicationFixtureFactory, JournalFixtureFactory
from portality.bll import DOAJ
from portality import constants
from doajtest.testdrive.factory import TestDrive
from portality import models
from portality.core import app
from portality import app_email
from doajtest.mocks.mock_mail import MockMail

from portality.events import consumers as c
from portality.models.event import Event
from portality.models import EditorGroup
from portality.lib import dates

class Notifications(TestDrive):
    def setup(self) -> dict:
        old_enable_email = app.config.get("ENABLE_EMAIL", False)
        old_app_mail = app_email.Mail

        app.config["ENABLE_EMAIL"] = True
        app_email.Mail = MockMail

        # admin
        un = self.create_random_str()
        pw1 = self.create_random_str()
        admin = models.Account.make_account(un + "@example.com", un, "Admin " + un, [constants.ROLE_ADMIN])
        admin.set_password(pw1)
        admin.save(blocking=True)

        # editor
        un = self.create_random_str()
        pw2 = self.create_random_str()
        ed = models.Account.make_account(un + "@example.com", un, "Editor " + un, [constants.ROLE_EDITOR])
        ed.set_password(pw2)
        ed.save(blocking=True)

        un = self.create_random_str()
        pw3 = self.create_random_str()
        ae = models.Account.make_account(un + "@example.com", un, "Associate " + un, [constants.ROLE_ASSOCIATE_EDITOR])
        ae.set_password(pw2)
        ae.save(blocking=True)

        un = self.create_random_str()
        pw4 = self.create_random_str()
        pub = models.Account.make_account(un + "@example.com", un, "Publisher " + un, [constants.ROLE_PUBLISHER])
        pub.set_password(pw4)
        pub.save(blocking=True)

        eg = EditorGroup(**{
            "name": self.create_random_str(),
            "maned": admin.id,
            "editor": ed.id,
            "associates": [ae.id]
        })
        eg.save(blocking=True)

        record = self._make_notifications(admin, ed, ae, pub, eg)

        app.config["ENABLE_EMAIL"] = old_enable_email
        app_email.Mail = old_app_mail

        return {
            "admin": {
                "username": admin.id,
                "password": pw1
            },
            "editor": {
                "username": ed.id,
                "password": pw2
            },
            "associate": {
                "username": ae.id,
                "password": pw3
            },
            "publisher": {
                "username": pub.id,
                "password": pw4
            },
            "editor_group": {
                "name": eg.name
            },
            "notifications": record
        }

    def _make_notifications(self, admin, editor, associate, publisher, eg):
        record = {}
        record.update(self._application_assed_accept_reject(admin, editor, associate, publisher, eg))
        record.update(self._application_assed_assigned(admin, editor, associate, publisher, eg))
        record.update(self._application_assed_in_progress(admin, editor, associate, publisher, eg))
        record.update(self._application_editor_accept_reject(admin, editor, associate, publisher, eg))
        record.update(self._application_editor_completed(admin, editor, associate, publisher, eg))
        record.update(self._application_editor_group_assigned(admin, editor, associate, publisher, eg))
        record.update(self._application_editor_in_progress(admin, editor, associate, publisher, eg))
        record.update(self._application_maned_ready(admin, editor, associate, publisher, eg))
        record.update(self._application_publisher_accepted(admin, editor, associate, publisher, eg))
        record.update(self._application_publisher_assigned(admin, editor, associate, publisher, eg))
        record.update(self._application_publisher_created(admin, editor, associate, publisher, eg))
        record.update(self._application_publisher_in_progress(admin, editor, associate, publisher, eg))
        record.update(self._application_publisher_quickreject(admin, editor, associate, publisher, eg))
        record.update(self._application_publisher_revision(admin, editor, associate, publisher, eg))
        record.update(self._bg_job_finished(admin, editor, associate, publisher, eg))
        record.update(self._journal_assed_assigned(admin, editor, associate, publisher, eg))
        record.update(self._journal_editor_group_assigned(admin, editor, associate, publisher, eg))
        record.update(self._update_request_editor_group_assigned(admin, editor, associate, publisher, eg))
        record.update(self._update_request_publisher_accepted(admin, editor, associate, publisher, eg))
        record.update(self._update_request_publisher_assigned(admin, editor, associate, publisher, eg))
        record.update(self._update_request_publisher_rejected(admin, editor, associate, publisher, eg))
        record.update(self._update_request_publisher_submitted(admin, editor, associate, publisher, eg))
        return record

    def _application_assed_accept_reject(self, admin, editor, associate, publisher, eg):
        application = ApplicationFixtureFactory.make_application_source({
            "admin": {
                "editor": associate.id,
                "application_status": constants.APPLICATION_STATUS_ACCEPTED,
            },
            "bibjson": {
                "title": c.ApplicationAssedAcceptRejectNotify.ID,
            },
            "id": c.ApplicationAssedAcceptRejectNotify.ID.replace(":", "_"),

        })
        event = Event(constants.EVENT_APPLICATION_STATUS, context={
            "application": application,
            "new_status": constants.APPLICATION_STATUS_ACCEPTED
        })
        consumer = c.ApplicationAssedAcceptRejectNotify()
        return {c.ApplicationAssedAcceptRejectNotify.ID : consumer.consume(event).id }

    def _application_assed_assigned(self, admin, editor, associate, publisher, eg):
        application = ApplicationFixtureFactory.make_application_source({
            "admin": {
                "editor": associate.id
            },
            "bibjson": {
                "title": c.ApplicationAssedAssignedNotify.ID,
            },
            "id": c.ApplicationAssedAssignedNotify.ID.replace(":", "_"),
        })
        event = Event(constants.EVENT_APPLICATION_ASSED_ASSIGNED, context={
            "application": application
        })
        consumer = c.ApplicationAssedAssignedNotify()
        return {c.ApplicationAssedAssignedNotify.ID : consumer.consume(event).id }

    def _application_assed_in_progress(self, admin, editor, associate, publisher, eg):
        application = ApplicationFixtureFactory.make_application_source({
            "admin": {
                "editor": associate.id
            },
            "bibjson": {
                "title": c.ApplicationAssedInprogressNotify.ID,
            },
            "id": c.ApplicationAssedInprogressNotify.ID.replace(":", "_"),
        })
        event = Event(constants.EVENT_APPLICATION_STATUS, context={
            "application": application
        })
        consumer = c.ApplicationAssedInprogressNotify()
        return {c.ApplicationAssedInprogressNotify.ID : consumer.consume(event).id }

    def _application_editor_accept_reject(self, admin, editor, associate, publisher, eg):
        application = ApplicationFixtureFactory.make_application_source({
            "admin": {
                "editor_group": eg.name,
                "editor": editor.id,
                "application_status": constants.APPLICATION_STATUS_REJECTED
            },
            "bibjson": {
                "title": c.ApplicationEditorAcceptRejectNotify.ID,
            },
            "id": c.ApplicationEditorAcceptRejectNotify.ID.replace(":", "_"),
        })
        event = Event(constants.EVENT_APPLICATION_STATUS, context={
            "application": application,
            "new_status": constants.APPLICATION_STATUS_REJECTED
        })
        consumer = c.ApplicationEditorAcceptRejectNotify()
        return {c.ApplicationEditorAcceptRejectNotify.ID : consumer.consume(event).id }

    def _application_editor_completed(self, admin, editor, associate, publisher, eg):
        application = ApplicationFixtureFactory.make_application_source({
            "admin": {
                "editor_group": eg.name,
                "editor": editor.id
            },
            "bibjson": {
                "title": c.ApplicationEditorCompletedNotify.ID,
            },
            "id": c.ApplicationEditorCompletedNotify.ID.replace(":", "_"),
        })
        event = Event(constants.EVENT_APPLICATION_STATUS, context={
            "application": application
        })
        consumer = c.ApplicationEditorCompletedNotify()
        return {c.ApplicationEditorCompletedNotify.ID : consumer.consume(event).id }

    def _application_editor_group_assigned(self, admin, editor, associate, publisher, eg):
        application = ApplicationFixtureFactory.make_application_source({
            "admin": {
                "editor_group": eg.name,
                "editor": editor.id
            },
            "bibjson": {
                "title": c.ApplicationEditorGroupAssignedNotify.ID,
            },
            "id": c.ApplicationEditorGroupAssignedNotify.ID.replace(":", "_"),
        })
        event = Event(constants.EVENT_APPLICATION_EDITOR_GROUP_ASSIGNED, context={
            "application": application
        })
        consumer = c.ApplicationEditorGroupAssignedNotify()
        return {c.ApplicationEditorGroupAssignedNotify.ID : consumer.consume(event).id }

    def _application_editor_in_progress(self, admin, editor, associate, publisher, eg):
        application = ApplicationFixtureFactory.make_application_source({
            "admin": {
                "editor_group": eg.name,
                "editor": editor.id
            },
            "bibjson": {
                "title": c.ApplicationEditorInProgressNotify.ID,
            },
            "id": c.ApplicationEditorInProgressNotify.ID.replace(":", "_"),
        })
        event = Event(constants.EVENT_APPLICATION_STATUS, context={
            "application": application
        })
        consumer = c.ApplicationEditorInProgressNotify()
        return {c.ApplicationEditorInProgressNotify.ID : consumer.consume(event).id }

    def _application_maned_ready(self, admin, editor, associate, publisher, eg):
        application = ApplicationFixtureFactory.make_application_source({
            "admin": {
                "editor_group": eg.name,
                "editor": associate.id
            },
            "bibjson": {
                "title": c.ApplicationManedReadyNotify.ID,
            },
            "id": c.ApplicationManedReadyNotify.ID.replace(":", "_"),
        })
        event = Event(constants.EVENT_APPLICATION_STATUS, context={
            "application": application
        })
        consumer = c.ApplicationManedReadyNotify()
        return {c.ApplicationManedReadyNotify.ID : consumer.consume(event).id }

    def _application_publisher_accepted(self, admin, editor, associate, publisher, eg):
        application = ApplicationFixtureFactory.make_application_source({
            "admin": {
                "owner": publisher.id,
            },
            "bibjson": {
                "title": c.ApplicationPublisherAcceptedNotify.ID,
            },
            "id": c.ApplicationPublisherAcceptedNotify.ID.replace(":", "_"),
        })
        event = Event(constants.EVENT_APPLICATION_STATUS, context={
            "application": application
        })
        consumer = c.ApplicationPublisherAcceptedNotify()
        return {c.ApplicationPublisherAcceptedNotify.ID : consumer.consume(event).id }

    def _application_publisher_assigned(self, admin, editor, associate, publisher, eg):
        application = ApplicationFixtureFactory.make_application_source({
            "admin": {
                "owner": publisher.id,
            },
            "bibjson": {
                "title": c.ApplicationPublisherAssignedNotify.ID,
            },
            "id": c.ApplicationPublisherAssignedNotify.ID.replace(":", "_"),
        })
        event = Event(constants.EVENT_APPLICATION_ASSED_ASSIGNED, context={
            "application": application
        })
        consumer = c.ApplicationPublisherAssignedNotify()
        return {c.ApplicationPublisherAssignedNotify.ID : consumer.consume(event).id }

    def _application_publisher_created(self, admin, editor, associate, publisher, eg):
        application = ApplicationFixtureFactory.make_application_source({
            "admin": {
                "owner": publisher.id,
            },
            "bibjson": {
                "title": c.ApplicationPublisherCreatedNotify.ID,
            },
            "id": c.ApplicationPublisherCreatedNotify.ID.replace(":", "_"),
        })
        event = Event(constants.EVENT_APPLICATION_CREATED, context={
            "application": application
        })
        consumer = c.ApplicationPublisherCreatedNotify()
        return {c.ApplicationPublisherCreatedNotify.ID : consumer.consume(event).id }

    def _application_publisher_in_progress(self, admin, editor, associate, publisher, eg):
        application = ApplicationFixtureFactory.make_application_source({
            "admin": {
                "owner": publisher.id,
            },
            "bibjson": {
                "title": c.ApplicationPublisherInprogressNotify.ID,
            },
            "id": c.ApplicationPublisherInprogressNotify.ID.replace(":", "_"),
        })
        event = Event(constants.EVENT_APPLICATION_STATUS, context={
            "application": application
        })
        consumer = c.ApplicationPublisherInprogressNotify()
        return {c.ApplicationPublisherInprogressNotify.ID : consumer.consume(event).id }

    def _application_publisher_quickreject(self, admin, editor, associate, publisher, eg):
        application = ApplicationFixtureFactory.make_application_source({
            "admin": {
                "owner": publisher.id,
            },
            "bibjson": {
                "title": c.ApplicationPublisherQuickRejectNotify.ID,
            },
            "id": c.ApplicationPublisherQuickRejectNotify.ID.replace(":", "_"),
        })
        event = Event(constants.EVENT_APPLICATION_STATUS, context={
            "application": application
        })
        consumer = c.ApplicationPublisherQuickRejectNotify()
        return {c.ApplicationPublisherQuickRejectNotify.ID: consumer.consume(event).id}

    def _application_publisher_revision(self, admin, editor, associate, publisher, eg):
        application = ApplicationFixtureFactory.make_application_source({
            "admin": {
                "owner": publisher.id,
            },
            "bibjson": {
                "title": c.ApplicationPublisherRevisionNotify.ID,
            },
            "id": c.ApplicationPublisherRevisionNotify.ID.replace(":", "_"),
        })
        event = Event(constants.EVENT_APPLICATION_STATUS, context={
            "application": application
        })
        consumer = c.ApplicationPublisherRevisionNotify()
        return {c.ApplicationPublisherRevisionNotify.ID: consumer.consume(event).id}

    def _bg_job_finished(self, admin, editor, associate, publisher, eg):
        job = models.BackgroundJob(**{
            "id": "bg:job_finished:notify",
            "user": admin.id,
            "action": "bg_job_finished_notify",
            "status": "complete"
        })

        event = Event(constants.BACKGROUND_JOB_FINISHED, context={
            "job": job
        })
        consumer = c.BGJobFinishedNotify()
        return {c.BGJobFinishedNotify.ID: consumer.consume(event).id}

    def _journal_assed_assigned(self, admin, editor, associate, publisher, eg):
        journal = JournalFixtureFactory.make_journal_source(overlay={
            "admin": {
                "editor": associate.id
            },
            "bibjson": {
                "title": c.JournalAssedAssignedNotify.ID,
            },
            "id": c.JournalAssedAssignedNotify.ID.replace(":", "_"),
        })
        event = Event(constants.EVENT_JOURNAL_ASSED_ASSIGNED, context={
            "journal": journal
        })
        consumer = c.JournalAssedAssignedNotify()
        return {c.JournalAssedAssignedNotify.ID: consumer.consume(event).id}

    def _journal_discontinuing_soon(self, admin, editor, associate, publisher, eg):
        journal = JournalFixtureFactory.make_journal_source(overlay={
            "admin": {
                "editor_group": eg.name
            },
            "bibjson": {
                "title": c.JournalDiscontinuingSoonNotify.ID,
            },
            "id": c.JournalDiscontinuingSoonNotify.ID.replace(":", "_"),
        })
        j = models.Journal(**journal)
        j.save(blocking=True)
        event = Event(constants.EVENT_JOURNAL_DISCONTINUING_SOON, context={
            "journal": journal.id,
            "discontinue_date": dates.now_str()
        })
        consumer = c.JournalDiscontinuingSoonNotify()
        j.delete()
        return {c.JournalDiscontinuingSoonNotify.ID: consumer.consume(event).id}

    def _journal_editor_group_assigned(self, admin, editor, associate, publisher, eg):
        journal = JournalFixtureFactory.make_journal_source(overlay={
            "admin": {
                "editor_group": eg.name,
                "editor": associate.id
            },
            "bibjson": {
                "title": c.JournalEditorGroupAssignedNotify.ID,
            },
            "id": c.JournalEditorGroupAssignedNotify.ID.replace(":", "_"),
        })
        event = Event(constants.EVENT_JOURNAL_EDITOR_GROUP_ASSIGNED, context={
            "journal": journal
        })
        consumer = c.JournalEditorGroupAssignedNotify()
        return {c.JournalEditorGroupAssignedNotify.ID: consumer.consume(event).id}

    def _update_request_editor_group_assigned(self, admin, editor, associate, publisher, eg):
        update_request = ApplicationFixtureFactory.make_update_request_source({
            "admin": {
                "editor_group": eg.name,
                "editor": associate.id
            },
            "bibjson": {
                "title": c.UpdateRequestManedEditorGroupAssignedNotify.ID,
            },
            "id": c.UpdateRequestManedEditorGroupAssignedNotify.ID.replace(":", "_"),
        })
        event = Event(constants.EVENT_APPLICATION_EDITOR_GROUP_ASSIGNED, context={
            "application": update_request
        })
        consumer = c.UpdateRequestManedEditorGroupAssignedNotify()
        return {c.UpdateRequestManedEditorGroupAssignedNotify.ID: consumer.consume(event).id}

    def _update_request_publisher_accepted(self, admin, editor, associate, publisher, eg):
        update_request = ApplicationFixtureFactory.make_update_request_source({
            "admin": {
                "owner": publisher.id,
            },
            "bibjson": {
                "title": c.UpdateRequestPublisherAcceptedNotify.ID,
            },
            "id": c.UpdateRequestPublisherAcceptedNotify.ID.replace(":", "_"),
        })
        event = Event(constants.EVENT_APPLICATION_STATUS, context={
            "application": update_request
        })
        consumer = c.UpdateRequestPublisherAcceptedNotify()
        return {c.UpdateRequestPublisherAcceptedNotify.ID: consumer.consume(event).id}

    def _update_request_publisher_assigned(self, admin, editor, associate, publisher, eg):
        update_request = ApplicationFixtureFactory.make_update_request_source({
            "admin": {
                "owner": publisher.id,
            },
            "bibjson": {
                "title": c.UpdateRequestPublisherAssignedNotify.ID,
            },
            "id": c.UpdateRequestPublisherAssignedNotify.ID.replace(":", "_"),
        })
        event = Event(constants.EVENT_APPLICATION_STATUS, context={
            "application": update_request
        })
        consumer = c.UpdateRequestPublisherAssignedNotify()
        return {c.UpdateRequestPublisherAssignedNotify.ID: consumer.consume(event).id}

    def _update_request_publisher_rejected(self, admin, editor, associate, publisher, eg):
        update_request = ApplicationFixtureFactory.make_update_request_source({
            "admin": {
                "owner": publisher.id,
            },
            "bibjson": {
                "title": c.UpdateRequestPublisherRejectedNotify.ID,
            },
            "id": c.UpdateRequestPublisherRejectedNotify.ID.replace(":", "_"),
        })
        event = Event(constants.EVENT_APPLICATION_STATUS, context={
            "application": update_request
        })
        consumer = c.UpdateRequestPublisherRejectedNotify()
        return {c.UpdateRequestPublisherRejectedNotify.ID: consumer.consume(event).id}

    def _update_request_publisher_submitted(self, admin, editor, associate, publisher, eg):
        update_request = ApplicationFixtureFactory.make_update_request_source({
            "admin": {
                "owner": publisher.id,
            },
            "bibjson": {
                "title": c.UpdateRequestPublisherSubmittedNotify.ID,
            },
            "id": c.UpdateRequestPublisherSubmittedNotify.ID.replace(":", "_"),
        })
        event = Event(constants.EVENT_APPLICATION_STATUS, context={
            "application": update_request
        })
        consumer = c.UpdateRequestPublisherSubmittedNotify()
        return {c.UpdateRequestPublisherSubmittedNotify.ID: consumer.consume(event).id}

    def teardown(self, params):
        models.Account.remove_by_id(params["admin"]["username"])
        models.Account.remove_by_id(params["editor"]["username"])
        models.Account.remove_by_id(params["associate"]["username"])
        models.Account.remove_by_id(params["publisher"]["username"])
        eg = EditorGroup.pull_by_key("name", params["editor_group"]["name"])
        eg.delete()

        for nid in params["notifications"].values():
            models.Notification.remove_by_id(nid)

        return {"status": "success"}

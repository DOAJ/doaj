# FIXME: these tests are no longer as useful as they once were because we always send the notification template

import logging
import re
from io import StringIO
from copy import deepcopy

from doajtest.fixtures.accounts import MANED_SOURCE
from portality import constants
from doajtest.fixtures import EditorGroupFixtureFactory, AccountFixtureFactory, ApplicationFixtureFactory, \
    JournalFixtureFactory
from doajtest.helpers import DoajTestCase
from portality import models
from portality.forms.application_forms import ApplicationFormFactory, JournalFormFactory
from portality.bll import DOAJ
from doajtest.mocks.bll_notification import InterceptNotifications
from portality.ui import templates

from portality.events.consumers.application_assed_inprogress_notify import ApplicationAssedInprogressNotify

UPDATE_REQUEST_SOURCE_TEST_1 = ApplicationFixtureFactory.make_update_request_source()
UPDATE_REQUEST_SOURCE_TEST_2 = ApplicationFixtureFactory.make_update_request_source()
UPDATE_REQUEST_SOURCE_TEST_3 = ApplicationFixtureFactory.make_update_request_source()

APPLICATION_SOURCE_TEST_1 = ApplicationFixtureFactory.make_application_source()
APPLICATION_SOURCE_TEST_2 = ApplicationFixtureFactory.make_application_source()
APPLICATION_SOURCE_TEST_3 = ApplicationFixtureFactory.make_application_source()

APPLICATION_FORM = ApplicationFixtureFactory.make_application_form()

JOURNAL_SOURCE_TEST_1 = JournalFixtureFactory.make_journal_source()
JOURNAL_SOURCE_TEST_2 = JournalFixtureFactory.make_journal_source()

EDITOR_GROUP_SOURCE = EditorGroupFixtureFactory.make_editor_group_source()
EDITOR_SOURCE = AccountFixtureFactory.make_editor_source()
ASSED1_SOURCE = AccountFixtureFactory.make_assed1_source()
ASSED2_SOURCE = AccountFixtureFactory.make_assed2_source()
ASSED3_SOURCE = AccountFixtureFactory.make_assed3_source()


#####################################################################
# Mocks required to make some of the lookups work
#####################################################################

@classmethod
def editor_group_pull_by_key(cls, field, value):
    eg = models.EditorGroup(**EDITOR_GROUP_SOURCE)
    return eg


@classmethod
def editor_group_pull(self, _id):
    return models.EditorGroup(**EDITOR_GROUP_SOURCE)


@classmethod
def editor_account_pull(self, _id):
    if _id == 'eddie':
        return models.Account(**EDITOR_SOURCE)
    if _id == 'associate':
        return models.Account(**ASSED1_SOURCE)
    if _id == 'associate_2':
        return models.Account(**ASSED2_SOURCE)
    if _id == 'associate_3':
        return models.Account(**ASSED3_SOURCE)
    if _id == "manny":
        return models.Account(**MANED_SOURCE)
    else:
        return ACTUAL_ACCOUNT_PULL(_id)


ACTUAL_ACCOUNT_PULL = models.Account.pull

# A regex string for searching the log entries
email_log_regex = r'template.*%s.*to:\[u{0,1}\'%s.*subject:.*%s'

# A string present in each email log entry (for counting them)
email_count_string = 'Email template'

NOTIFICATIONS_INTERCEPT = []


class TestPublicApplicationEmails(DoajTestCase):
    def setUp(self):
        super(TestPublicApplicationEmails, self).setUp()

        # Register a new log handler so we can inspect the info logs
        self.info_stream = StringIO()
        self.read_info = logging.StreamHandler(self.info_stream)
        self.read_info.setLevel(logging.INFO)
        self.app_test.logger.addHandler(self.read_info)

        self.notifications_service = DOAJ.notificationsService
        NOTIFICATIONS_INTERCEPT.clear()
        DOAJ.notificationsService = lambda: InterceptNotifications(NOTIFICATIONS_INTERCEPT)
        self.svc = DOAJ.notificationsService()

    def tearDown(self):
        super(TestPublicApplicationEmails, self).tearDown()

        # Blank the info_stream and remove the error handler from the app
        self.info_stream.truncate(0)
        self.app_test.logger.removeHandler(self.read_info)

        DOAJ.notificationsService = self.notifications_service

    def test_01_public_application_email(self):
        application = models.Application(**APPLICATION_SOURCE_TEST_1)

        account = models.Account()
        account.set_id("testing")
        account.set_email("testing@example.com")
        account.save(blocking=True)

        application.set_owner(account.id)

        # Construct an application form
        fc = ApplicationFormFactory.context("public")
        processor = fc.processor(source=application)

        # Emails are sent during the finalise stage, and requires the app context to build URLs
        with self.app_test.test_request_context():
            processor.finalise(account)
        # Use the captured info stream to get email send logs
        info_stream_contents = self.info_stream.getvalue()

        # We expect one email sent:
        #   * to the applicant, informing them the application was received
        public_template = re.escape(templates.EMAIL_NOTIFICATION)
        public_to = re.escape(account.email)
        public_subject = re.escape("Directory of Open Access Journals - Your application for " + ", ".join(
            issn for issn in processor.source.bibjson().issns()) + " to DOAJ has been received")
        public_email_matched = re.search(email_log_regex % (public_template, public_to, public_subject),
                                         info_stream_contents,
                                         re.DOTALL)
        assert bool(public_email_matched), info_stream_contents
        assert len(re.findall(email_count_string, info_stream_contents)) == 1


class TestApplicationReviewEmails(DoajTestCase):

    def setUp(self):
        super(TestApplicationReviewEmails, self).setUp()

        self.editor_group_pull_by_key = models.EditorGroup.pull_by_key
        self.editor_group_pull = models.EditorGroup.pull
        models.EditorGroup.pull_by_key = editor_group_pull_by_key
        models.EditorGroup.pull = editor_group_pull

        self.editor_account_pull = models.Account.pull
        models.Account.pull = editor_account_pull

        # Register a new log handler so we can inspect the info logs
        self.info_stream = StringIO()
        self.read_info = logging.StreamHandler(self.info_stream)
        self.read_info.setLevel(logging.INFO)
        self.app_test.logger.addHandler(self.read_info)

        self.enable_publisher_email = self.app_test.config["ENABLE_PUBLISHER_EMAIL"]
        self.app_test.config["ENABLE_PUBLISHER_EMAIL"] = True

        self.notifications_service = DOAJ.notificationsService
        NOTIFICATIONS_INTERCEPT.clear()
        DOAJ.notificationsService = lambda: InterceptNotifications(NOTIFICATIONS_INTERCEPT)
        self.svc = DOAJ.notificationsService()

    def tearDown(self):
        super(TestApplicationReviewEmails, self).tearDown()

        models.EditorGroup.pull_by_key = self.editor_group_pull_by_key
        models.EditorGroup.pull = self.editor_group_pull
        models.Account.pull = self.editor_account_pull

        # Blank the info_stream and remove the error handler from the app
        self.info_stream.truncate(0)
        self.app_test.logger.removeHandler(self.read_info)

        self.app_test.config["ENABLE_PUBLISHER_EMAIL"] = self.enable_publisher_email

        DOAJ.notificationsService = self.notifications_service

    def test_01_maned_review_emails(self):
        """ Ensure the Managing Editor's application review form sends the right emails"""
        acc = models.Account()
        acc.set_id("contextuser")
        acc.add_role("admin")
        with self._make_and_push_test_context_manager(acc=acc):
            # If an application has been set to 'ready' but is returned to 'in progress',
            # an email is sent to the editor and assigned associate editor
            ready_application = models.Application(**APPLICATION_SOURCE_TEST_1)
            ready_application.set_application_status(constants.APPLICATION_STATUS_READY)
            ready_application.application_type = constants.APPLICATION_TYPE_NEW_APPLICATION
            ready_application.remove_current_journal()

            owner = models.Account()
            owner.set_id(ready_application.owner)
            owner.set_name("Test Name")
            owner.set_email("test@example.com")
            owner.save(blocking=True)

            # Construct an application form
            fc = ApplicationFormFactory.context("admin")
            processor = fc.processor(source=ready_application)

            # Make changes to the application status via the form
            processor.form.application_status.data = constants.APPLICATION_STATUS_IN_PROGRESS

            # Emails are sent during the finalise stage, and requires the app context to build URLs
            processor.finalise(acc)

            # Use the captured info stream to get email send logs
            info_stream_contents = self.info_stream.getvalue()

            # Prove we went from to and from the right statuses
            assert processor.source.application_status == constants.APPLICATION_STATUS_READY
            assert processor.target.application_status == constants.APPLICATION_STATUS_IN_PROGRESS

            # We expect two emails sent:
            #   * to the editor, informing them an application has been bounced from ready back to in progress.
            #   * to the associate editor, informing them the same
            assert len(
                NOTIFICATIONS_INTERCEPT) == 2  # this will change when more of this file is run through the notifications system

            ### editor in progress notification and email
            notification = NOTIFICATIONS_INTERCEPT.pop()
            assert notification.who == "eddie"
            assert notification.long is not None  # this and action are hard to predict, so lets just check they are set
            assert notification.action is not None
            assert notification.classification == constants.NOTIFICATION_CLASSIFICATION_STATUS_CHANGE

            editor_template = re.escape(templates.EMAIL_NOTIFICATION)
            editor_to = re.escape('eddie@example.com')
            editor_subject = re.escape("Application (" + ", ".join(issn for issn in
                                                                   processor.source.bibjson().issns()) + ") reverted to 'In Progress' by Managing Editor\n")
            editor_email_matched = re.search(email_log_regex % (editor_template, editor_to, editor_subject),
                                             info_stream_contents,
                                             re.DOTALL)
            assert bool(editor_email_matched)

            ### associate editor in progress notification and email
            assert len(
                NOTIFICATIONS_INTERCEPT) == 1  # this will change when more of this file is run through the notifications system
            notification = NOTIFICATIONS_INTERCEPT.pop()
            assert notification.who == "associate"
            assert notification.long is not None  # this and action are hard to predict, so lets just check they are set
            assert notification.action is not None
            assert notification.classification == constants.NOTIFICATION_CLASSIFICATION_STATUS_CHANGE

            assoc_editor_template = re.escape(templates.EMAIL_NOTIFICATION)
            assoc_editor_to = re.escape('associate@example.com')
            assoc_editor_subject = re.escape(
                self.svc.short_notification(ApplicationAssedInprogressNotify.ID).replace("{issns}", ", ".join(
                    issn for issn in
                    processor.source.bibjson().issns())) + "\n")  # "an application assigned to you has not passed review."
            assoc_editor_email_matched = re.search(
                email_log_regex % (assoc_editor_template, assoc_editor_to, assoc_editor_subject),
                info_stream_contents,
                re.DOTALL)
            assert bool(assoc_editor_email_matched)
            assert len(re.findall(email_count_string, info_stream_contents)) == 2

            # Clear the stream for the next part
            self.info_stream.truncate(0)

            # If our ManEd is doing an editor's job - setting from 'completed' but is returned to 'in progress',
            # an email is sent to the editor in charge of the application's group and assigned associate editor
            completed_application = models.Suggestion(**APPLICATION_SOURCE_TEST_1)
            completed_application.set_application_status(constants.APPLICATION_STATUS_COMPLETED)

            # Construct an application form
            fc = ApplicationFormFactory.context("admin")
            processor = fc.processor(source=completed_application)
            # fc = formcontext.ApplicationFormFactory.get_form_context(
            #     role="admin",
            #     source=completed_application
            # )
            # assert isinstance(fc, formcontext.ManEdApplicationReview)

            # Make changes to the application status via the form
            processor.form.application_status.data = constants.APPLICATION_STATUS_IN_PROGRESS

            # Emails are sent during the finalise stage, and requires the app context to build URLs
            processor.finalise(acc)

            # Use the captured info stream to get email send logs
            info_stream_contents = self.info_stream.getvalue()

            # Prove we went from to and from the right statuses
            assert processor.source.application_status == constants.APPLICATION_STATUS_COMPLETED
            assert processor.target.application_status == constants.APPLICATION_STATUS_IN_PROGRESS

            # We expect two emails sent:
            #   * to the editor, informing them an application has been bounced from completed back to in progress.
            #   * to the associate editor, informing them the same
            assert len(
                NOTIFICATIONS_INTERCEPT) == 2  # this will change when more of this file is run through the notifications system

            ### editor in progress notification and email
            notification = NOTIFICATIONS_INTERCEPT.pop()
            assert notification.who == "eddie"
            assert notification.long is not None  # this and action are hard to predict, so lets just check they are set
            assert notification.action is not None
            assert notification.classification == constants.NOTIFICATION_CLASSIFICATION_STATUS_CHANGE

            editor_template = re.escape(templates.EMAIL_NOTIFICATION)
            editor_to = re.escape('eddie@example.com')
            editor_subject = re.escape(
                "Directory of Open Access Journals - Application ({}) reverted to 'In Progress' by Managing Editor".format(
                    ', '.join(issn for issn in processor.source.bibjson().issns())))
            editor_email_matched = re.search(email_log_regex % (editor_template, editor_to, editor_subject),
                                             info_stream_contents,
                                             re.DOTALL)
            assert bool(editor_email_matched)

            ### associate editor in progress notification and email
            assert len(
                NOTIFICATIONS_INTERCEPT) == 1  # this will change when more of this file is run through the notifications system
            notification = NOTIFICATIONS_INTERCEPT.pop()
            assert notification.who == "associate"
            assert notification.long is not None  # this and action are hard to predict, so lets just check they are set
            assert notification.action is not None
            assert notification.classification == constants.NOTIFICATION_CLASSIFICATION_STATUS_CHANGE

            assoc_editor_template = re.escape(templates.EMAIL_NOTIFICATION)
            assoc_editor_to = re.escape('associate@example.com')
            assoc_editor_subject = re.escape(
                self.svc.short_notification(ApplicationAssedInprogressNotify.ID).replace("{issns}", ", ".join(
                    issn for issn in
                    processor.source.bibjson().issns())) + "\n")  # "an application assigned to you has not passed review."
            assoc_editor_email_matched = re.search(
                email_log_regex % (assoc_editor_template, assoc_editor_to, assoc_editor_subject),
                info_stream_contents,
                re.DOTALL)
            assert bool(assoc_editor_email_matched)
            assert len(re.findall(email_count_string, info_stream_contents)) == 2

            # Clear the stream for the next part
            self.info_stream.truncate(0)

            # When an application is assigned to an associate editor for the first time, email the assoc_ed and publisher.

            # Refresh the application form - create a fresh application without an editor assigned.
            no_ed = deepcopy(APPLICATION_SOURCE_TEST_1)
            del no_ed['admin']['editor']
            del no_ed['admin']['related_journal']
            no_ed['admin']['application_status'] = 'pending'
            no_ed['admin']['application_type'] = 'new_application'
            no_ed = models.Application(**no_ed)

            fc = ApplicationFormFactory.context("admin")
            processor = fc.processor(source=no_ed)
            # fc = formcontext.ApplicationFormFactory.get_form_context(role="admin", source=no_ed)

            # Assign the associate editor and save the form
            processor.form.editor.data = "associate_3"

            processor.finalise(acc)

            info_stream_contents = self.info_stream.getvalue()

            # check the associate was changed
            assert processor.target.editor == "associate_3"

            # We expect 2 emails to be sent:
            #   * to the AssEd who's been assigned,
            #   * and to the publisher informing them there's an editor assigned.
            assEd_template = re.escape(templates.EMAIL_NOTIFICATION)
            assEd_to = re.escape(models.Account.pull('associate_3').email)
            assEd_subject = re.escape('Directory of Open Access Journals - New application ({}) assigned to you'.format(
                ', '.join(issn for issn in processor.source.bibjson().issns())))

            assEd_email_matched = re.search(email_log_regex % (assEd_template, assEd_to, assEd_subject),
                                            info_stream_contents,
                                            re.DOTALL)
            assert bool(assEd_email_matched), info_stream_contents.strip('\x00')

            assert len(re.findall(email_count_string, info_stream_contents)) == 1

            # Clear the stream for the next part
            self.info_stream.truncate(0)

            # Refresh the application form
            fc = ApplicationFormFactory.context("admin")
            processor = fc.processor(source=ready_application)
            # fc = formcontext.ApplicationFormFactory.get_form_context(role="admin", source=ready_application)

            # Next, if we change the editor group or assigned editor, emails should be sent to editors, & NOT the publisher
            processor.form.editor_group.data = "Test Editor Group"
            processor.form.editor.data = "associate_3"

            processor.finalise(acc)
            info_stream_contents = self.info_stream.getvalue()

            # check the associate was changed
            assert processor.target.editor == "associate_3"

            # We expect 2 emails to be sent:
            #   * to the editor of the assigned group,
            #   * to the AssEd who's been assigned
            editor_template = re.escape(templates.EMAIL_NOTIFICATION)
            editor_to = re.escape('eddie@example.com')
            editor_subject = re.escape(
                'Directory of Open Access Journals - New application ({}) assigned to your group'.format(
                    ', '.join(issn for issn in processor.source.bibjson().issns())))

            editor_email_matched = re.search(email_log_regex % (editor_template, editor_to, editor_subject),
                                             info_stream_contents,
                                             re.DOTALL)
            assert bool(editor_email_matched)

            assEd_template = re.escape(templates.EMAIL_NOTIFICATION)
            assEd_to = re.escape(models.Account.pull('associate_3').email)
            assEd_subject = re.escape('Directory of Open Access Journals - New application ({}) assigned to you'.format(
                ', '.join(issn for issn in processor.source.bibjson().issns())))
            assEd_email_matched = re.search(email_log_regex % (assEd_template, assEd_to, assEd_subject),
                                            info_stream_contents,
                                            re.DOTALL)
            assert bool(assEd_email_matched), info_stream_contents.strip('\x00')
            assert len(re.findall(email_count_string, info_stream_contents)) == 2

            # Clear the stream for the next part
            self.info_stream.truncate(0)

            # A Managing Editor will notify other ManEds when they set an application to 'Ready'
            # Refresh the application form
            pending_application = models.Suggestion(**APPLICATION_SOURCE_TEST_2)
            jid = pending_application.current_journal
            journal_source = JOURNAL_SOURCE_TEST_1
            journal_source["id"] = jid
            journal_source['admin']["in_doaj"] = True
            current_journal = models.Journal(**journal_source)
            current_journal.save()

            # Create a ManEd to be in charge of the Editor Group for this application
            acc = models.Account(**AccountFixtureFactory.make_managing_editor_source())
            acc.set_id('manny')  # to match the Editor Group defaults   # Fixme: better fixtures!
            acc.save(blocking=True)

            fc = ApplicationFormFactory.context("admin")
            processor = fc.processor(source=pending_application)
            # fc = formcontext.ApplicationFormFactory.get_form_context(role="admin", source=pending_application)

            # Make changes to the application status via the form
            processor.form.application_status.data = constants.APPLICATION_STATUS_READY

            processor.finalise(acc)
            info_stream_contents = self.info_stream.getvalue()

            # We expect one email to be sent here:
            #   * to the ManEd in charge of the assigned Editor Group, saying an application is ready
            manEd_template = re.escape(templates.EMAIL_NOTIFICATION)
            manEd_to = re.escape(acc.email)
            manEd_subject = re.escape('Directory of Open Access Journals - Application ({}) marked as ready'.format(
                ', '.join(issn for issn in processor.source.bibjson().issns())))

            manEd_email_matched = re.search(email_log_regex % (manEd_template, manEd_to, manEd_subject),
                                            info_stream_contents,
                                            re.DOTALL)
            assert bool(manEd_email_matched)
            assert len(re.findall(email_count_string, info_stream_contents)) == 1

            # Clear the stream for the next part
            self.info_stream.truncate(0)

            # Finally, a Managing Editor will also trigger emails to the publisher when they accept an Application

            # Refresh the application form
            fc = ApplicationFormFactory.context("admin")
            processor = fc.processor(source=no_ed)
            processor.form.application_status.data = constants.APPLICATION_STATUS_ACCEPTED

            processor.finalise(acc)
            info_stream_contents = self.info_stream.getvalue()

            # We expect 1 email to be sent:
            #   * to the publisher, informing them of the journal's acceptance
            publisher_template = re.escape(templates.EMAIL_NOTIFICATION)
            publisher_to = re.escape(owner.email)
            publisher_subject = re.escape(
                'Directory of Open Access Journals - Your journal ({}) has been accepted'.format(
                    ', '.join(issn for issn in processor.source.bibjson().issns())))

            publisher_email_matched = re.search(email_log_regex % (publisher_template, publisher_to, publisher_subject),
                                                info_stream_contents,
                                                re.DOTALL)
            assert bool(publisher_email_matched), (publisher_email_matched, info_stream_contents)
            assert len(re.findall(email_count_string, info_stream_contents)) == 2   # expecting a second email too, not tested for above

    def test_02_ed_review_emails(self):
        """ Ensure the Editor's application review form sends the right emails"""
        acc = models.Account()
        acc.set_id("contextuser")
        acc.add_role("editor")
        with self._make_and_push_test_context_manager(acc=acc):
            # ctx = self._make_and_push_test_context(acc=acc)

            # If an application has been set to 'ready' from another status, the ManEds are notified
            pending_application = models.Suggestion(**APPLICATION_SOURCE_TEST_2)
            pending_application.remove_current_journal()

            owner = models.Account()
            owner.set_id(pending_application.owner)
            owner.set_name("Test Name")
            owner.set_email("test@example.com")
            owner.save(blocking=True)

            maned = models.Account()
            maned.set_id(EDITOR_GROUP_SOURCE.get("maned"))
            maned.set_email("maned@example.com")
            maned.save(blocking=True)

            # Construct an application form
            fc = ApplicationFormFactory.context("editor")
            processor = fc.processor(source=pending_application)
            # fc = formcontext.ApplicationFormFactory.get_form_context(
            #     role="editor",
            #     source=pending_application
            # )
            # assert isinstance(fc, formcontext.EditorApplicationReview)

            # Make changes to the application status via the form
            processor.form.application_status.data = constants.APPLICATION_STATUS_READY

            processor.finalise()
            info_stream_contents = self.info_stream.getvalue()

            # We expect one email to be sent here:
            #   * to the ManEds, saying an application is ready
            manEd_template = templates.EMAIL_NOTIFICATION
            manEd_to = re.escape("maned@example.com")
            manEd_subject = re.escape('Application ({}) marked as ready'.format(
                ', '.join(issn for issn in processor.source.bibjson().issns())))

            manEd_email_matched = re.search(email_log_regex % (manEd_template, manEd_to, manEd_subject),
                                            info_stream_contents,
                                            re.DOTALL)
            assert bool(manEd_email_matched)
            assert len(re.findall(email_count_string, info_stream_contents)) == 1

            # Clear the stream for the next part
            self.info_stream.truncate(0)

            # When an application is assigned to an associate editor for the first time, email the assoc_ed and publisher.

            # Refresh the application form
            no_ed = deepcopy(pending_application.data)
            del no_ed['admin']['editor']
            no_ed = models.Suggestion(**no_ed)
            fc = ApplicationFormFactory.context("editor")
            processor = fc.processor(source=no_ed)
            # fc = formcontext.ApplicationFormFactory.get_form_context(role="admin", source=no_ed)

            # Assign the associate editor and save the form
            processor.form.editor.data = "associate_3"

            processor.finalise()
            info_stream_contents = self.info_stream.getvalue()

            # check the associate was changed
            assert processor.target.editor == "associate_3"

            # We expect 2 emails to be sent:
            #   * to the AssEd who's been assigned,
            #   * and to the publisher informing them there's an editor assigned.
            assEd_template = templates.EMAIL_NOTIFICATION
            assEd_to = re.escape(models.Account.pull('associate_3').email)
            assEd_subject = re.escape('New application ({}) assigned to you'.format(
                ', '.join(issn for issn in processor.source.bibjson().issns())))

            assEd_email_matched = re.search(email_log_regex % (assEd_template, assEd_to, assEd_subject),
                                            info_stream_contents,
                                            re.DOTALL)
            assert bool(assEd_email_matched), info_stream_contents.strip('\x00')
            assert len(re.findall(email_count_string, info_stream_contents)) == 1

            # Clear the stream for the next part
            self.info_stream.truncate(0)

            # Editors can also reassign applications to different associate editors.
            fc = ApplicationFormFactory.context("editor")
            processor = fc.processor(source=models.Suggestion(**APPLICATION_SOURCE_TEST_2))
            processor.form.editor.data = "associate_2"
            processor.finalise()
            info_stream_contents = self.info_stream.getvalue()

            # check the associate was changed
            assert processor.target.editor == "associate_2"

            # We expect 1 email to be sent:
            #   * to the AssEd who's been assigned,
            assEd_template = templates.EMAIL_NOTIFICATION
            assEd_to = re.escape(models.Account.pull('associate_2').email)
            assEd_subject = re.escape('New application ({}) assigned to you'.format(
                ', '.join(issn for issn in processor.source.bibjson().issns())))

            assEd_email_matched = re.search(email_log_regex % (assEd_template, assEd_to, assEd_subject),
                                            info_stream_contents,
                                            re.DOTALL)
            assert bool(assEd_email_matched), info_stream_contents.strip('\x00')
            assert len(re.findall(email_count_string, info_stream_contents)) == 1

            # Clear the stream for the next part
            self.info_stream.truncate(0)

            # When an editor changes the state from 'completed' to 'in progress', the assigned associate is emailed.
            completed_application = models.Suggestion(**UPDATE_REQUEST_SOURCE_TEST_2)
            completed_application.set_application_status(constants.APPLICATION_STATUS_COMPLETED)

            # Construct an application form
            fc = ApplicationFormFactory.context("editor")
            processor = fc.processor(source=completed_application)

            # Make changes to the application status via the form
            processor.form.application_status.data = constants.APPLICATION_STATUS_IN_PROGRESS

            # Emails are sent during the finalise stage, and requires the app context to build URLs
            processor.finalise()

            # Use the captured info stream to get email send logs
            info_stream_contents = self.info_stream.getvalue()

            # Prove we went from to and from the right statuses
            assert processor.source.application_status == constants.APPLICATION_STATUS_COMPLETED
            assert processor.target.application_status == constants.APPLICATION_STATUS_IN_PROGRESS

            # We expect two email to be sent:
            #   * to the associate editor, informing them the application has been bounced back to in progress.
            #   * to the editor telling them an application has reverted to in progress
            assoc_editor_template = re.escape(templates.EMAIL_NOTIFICATION)
            assoc_editor_to = re.escape('associate@example.com')
            assoc_editor_subject = re.escape('One of your applications ({}) has not passed review'.format(
                ', '.join(issn for issn in processor.source.bibjson().issns())))
            assoc_editor_email_matched = re.search(
                email_log_regex % (assoc_editor_template, assoc_editor_to, assoc_editor_subject),
                info_stream_contents,
                re.DOTALL)
            assert bool(assoc_editor_email_matched)

            assert len(re.findall(email_count_string, info_stream_contents)) == 2

    def test_03_assoc_ed_review_emails(self):
        """ Ensure the Associate Editor's application review form sends the right emails"""
        acc = models.Account()
        acc.set_id("contextuser")
        acc.add_role("associate_editor")
        with self._make_and_push_test_context_manager(acc=acc):
            # If an application has been set to 'in progress' from 'pending', the publisher is notified
            pending_application = models.Suggestion(**APPLICATION_SOURCE_TEST_3)
            pending_application.remove_current_journal()

            owner = models.Account()
            owner.set_id(pending_application.owner)
            owner.set_name("Test Name")
            owner.set_email("test@example.com")
            owner.save(blocking=True)

            # Construct an application form
            fc = ApplicationFormFactory.context("associate_editor")
            processor = fc.processor(source=pending_application)

            # Make changes to the application status via the form
            processor.form.application_status.data = constants.APPLICATION_STATUS_IN_PROGRESS

            processor.finalise()
            info_stream_contents = self.info_stream.getvalue()

            # We expect no emails
            assert len(re.findall(email_count_string, info_stream_contents)) == 0

            # Clear the stream for the next part
            self.info_stream.truncate(0)

            # When the application is then set to 'completed', the editor in charge of this group is informed
            processor.form.application_status.data = constants.APPLICATION_STATUS_COMPLETED

            processor.finalise()
            info_stream_contents = self.info_stream.getvalue()

            # We expect one email sent:
            #   * to the editor, informing them an application has been completed by an Associate Editor
            editor_template = re.escape(templates.EMAIL_NOTIFICATION)
            editor_to = re.escape('eddie@example.com')
            editor_subject = re.escape(
                'Directory of Open Access Journals - Application ({}) marked as completed'.format(
                    ', '.join(issn for issn in processor.source.bibjson().issns())))
            editor_email_matched = re.search(email_log_regex % (editor_template, editor_to, editor_subject),
                                             info_stream_contents,
                                             re.DOTALL)
            assert bool(editor_email_matched)
            assert len(re.findall(email_count_string, info_stream_contents)) == 1


class TestUpdateRequestReviewEmails(DoajTestCase):

    def setUp(self):
        super(TestUpdateRequestReviewEmails, self).setUp()

        self.editor_group_pull_by_key = models.EditorGroup.pull_by_key
        self.editor_group_pull = models.EditorGroup.pull
        models.EditorGroup.pull_by_key = editor_group_pull_by_key
        models.EditorGroup.pull = editor_group_pull

        self.editor_account_pull = models.Account.pull
        models.Account.pull = editor_account_pull

        # Register a new log handler so we can inspect the info logs
        self.info_stream = StringIO()
        self.read_info = logging.StreamHandler(self.info_stream)
        self.read_info.setLevel(logging.INFO)
        self.app_test.logger.addHandler(self.read_info)

        self.enable_publisher_email = self.app_test.config["ENABLE_PUBLISHER_EMAIL"]
        self.app_test.config["ENABLE_PUBLISHER_EMAIL"] = True

        self.notifications_service = DOAJ.notificationsService
        NOTIFICATIONS_INTERCEPT.clear()
        DOAJ.notificationsService = lambda: InterceptNotifications(NOTIFICATIONS_INTERCEPT)
        self.svc = DOAJ.notificationsService()

    def tearDown(self):
        super(TestUpdateRequestReviewEmails, self).tearDown()

        models.EditorGroup.pull_by_key = self.editor_group_pull_by_key
        models.EditorGroup.pull = self.editor_group_pull
        models.Account.pull = self.editor_account_pull

        # Blank the info_stream and remove the error handler from the app
        self.info_stream.truncate(0)
        self.app_test.logger.removeHandler(self.read_info)

        self.app_test.config["ENABLE_PUBLISHER_EMAIL"] = self.enable_publisher_email

    def test_01_maned_review_emails(self):
        """ Ensure the Managing Editor's application review form sends the right emails"""
        acc = models.Account()
        acc.set_id("contextuser")
        acc.add_role("admin")
        with self._make_and_push_test_context_manager(acc=acc):
            # If an application has been set to 'ready' but is returned to 'in progress',
            # an email is sent to the editor and assigned associate editor
            ready_application = models.Suggestion(**UPDATE_REQUEST_SOURCE_TEST_1)
            ready_application.set_application_status(constants.APPLICATION_STATUS_READY)
            jid = ready_application.current_journal
            journal_source = JOURNAL_SOURCE_TEST_1
            journal_source["id"] = jid
            journal_source['admin']["in_doaj"] = True
            current_journal = models.Journal(**journal_source)
            current_journal.save()

            owner = models.Account()
            owner.set_id(ready_application.owner)
            owner.set_name("Test Name")
            owner.set_email("test@example.com")
            owner.save(blocking=True)

            maned = models.Account()
            maned.set_id(EDITOR_GROUP_SOURCE.get("maned"))
            maned.set_email("maned@example.com")
            maned.save(blocking=True)

            # Construct an application form
            fc = ApplicationFormFactory.context("admin")
            processor = fc.processor(source=ready_application)

            # Make changes to the application status via the form
            processor.form.application_status.data = constants.APPLICATION_STATUS_IN_PROGRESS

            # Emails are sent during the finalise stage, and requires the app context to build URLs
            processor.finalise(acc)

            # Use the captured info stream to get email send logs
            info_stream_contents = self.info_stream.getvalue()

            # Prove we went from to and from the right statuses
            assert processor.source.application_status == constants.APPLICATION_STATUS_READY
            assert processor.target.application_status == constants.APPLICATION_STATUS_IN_PROGRESS

            # We expect two emails sent:
            #   * to the editor, informing them an application has been bounced from ready back to in progress.
            #   * to the associate editor, informing them the same
            assert len(
                NOTIFICATIONS_INTERCEPT) == 2  # this will change when more of this file is run through the notifications system

            ### editor in progress notification and email
            notification = NOTIFICATIONS_INTERCEPT.pop()
            assert notification.who == "eddie"
            assert notification.long is not None  # this and action are hard to predict, so lets just check they are set
            assert notification.action is not None
            assert notification.classification == constants.NOTIFICATION_CLASSIFICATION_STATUS_CHANGE

            editor_template = re.escape(templates.EMAIL_NOTIFICATION)
            editor_to = re.escape('eddie@example.com')
            editor_subject = re.escape("Application ({}) reverted to 'In Progress' by Managing Editor".format(
                ', '.join(issn for issn in processor.source.bibjson().issns())))
            editor_email_matched = re.search(email_log_regex % (editor_template, editor_to, editor_subject),
                                             info_stream_contents,
                                             re.DOTALL)
            assert bool(editor_email_matched)

            ### associate editor in progress notification and email
            assert len(
                NOTIFICATIONS_INTERCEPT) == 1  # this will change when more of this file is run through the notifications system
            notification = NOTIFICATIONS_INTERCEPT.pop()
            assert notification.who == "associate"
            assert notification.long is not None  # this and action are hard to predict, so lets just check they are set
            assert notification.action is not None
            assert notification.classification == constants.NOTIFICATION_CLASSIFICATION_STATUS_CHANGE

            assoc_editor_template = re.escape(templates.EMAIL_NOTIFICATION)
            assoc_editor_to = re.escape('associate@example.com')
            assoc_editor_subject = re.escape(self.svc.short_notification(
                ApplicationAssedInprogressNotify.ID).replace("{issns}", ", ".join(issn for issn in
                                                                                  processor.target.bibjson().issns())) + "\n")  # "an application assigned to you has not passed review."
            assoc_editor_email_matched = re.search(
                email_log_regex % (assoc_editor_template, assoc_editor_to, assoc_editor_subject),
                info_stream_contents,
                re.DOTALL)
            assert bool(assoc_editor_email_matched)
            assert len(re.findall(email_count_string, info_stream_contents)) == 2

            # Clear the stream for the next part
            self.info_stream.truncate(0)

            # If our ManEd is doing an editor's job - setting from 'completed' but is returned to 'in progress',
            # an email is sent to the editor in charge of the application's group and assigned associate editor
            completed_application = models.Suggestion(**UPDATE_REQUEST_SOURCE_TEST_1)
            completed_application.set_application_status(constants.APPLICATION_STATUS_COMPLETED)

            # Construct an application form
            fc = ApplicationFormFactory.context("admin")
            processor = fc.processor(source=completed_application)
            # fc = formcontext.ApplicationFormFactory.get_form_context(
            #     role="admin",
            #     source=completed_application
            # )
            # assert isinstance(fc, formcontext.ManEdApplicationReview)

            # Make changes to the application status via the form
            processor.form.application_status.data = constants.APPLICATION_STATUS_IN_PROGRESS

            # Emails are sent during the finalise stage, and requires the app context to build URLs
            processor.finalise(acc)

            # Use the captured info stream to get email send logs
            info_stream_contents = self.info_stream.getvalue()

            # Prove we went from to and from the right statuses
            assert processor.source.application_status == constants.APPLICATION_STATUS_COMPLETED
            assert processor.target.application_status == constants.APPLICATION_STATUS_IN_PROGRESS

            # We expect two emails sent:
            #   * to the editor, informing them an application has been bounced from completed back to in progress.
            #   * to the associate editor, informing them the same
            assert len(
                NOTIFICATIONS_INTERCEPT) == 2  # this will change when more of this file is run through the notifications system

            ### editor in progress notification and email
            notification = NOTIFICATIONS_INTERCEPT.pop()
            assert notification.who == "eddie"
            assert notification.long is not None  # this and action are hard to predict, so lets just check they are set
            assert notification.action is not None
            assert notification.classification == constants.NOTIFICATION_CLASSIFICATION_STATUS_CHANGE

            editor_template = re.escape(templates.EMAIL_NOTIFICATION)
            editor_to = re.escape('eddie@example.com')
            editor_subject = re.escape("Application ({}) reverted to 'In Progress' by Managing Editor".format(
                ', '.join(issn for issn in processor.source.bibjson().issns())))
            editor_email_matched = re.search(email_log_regex % (editor_template, editor_to, editor_subject),
                                             info_stream_contents,
                                             re.DOTALL)
            assert bool(editor_email_matched)

            ### associate editor in progress notification and email
            assert len(
                NOTIFICATIONS_INTERCEPT) == 1  # this will change when more of this file is run through the notifications system
            notification = NOTIFICATIONS_INTERCEPT.pop()
            assert notification.who == "associate"
            assert notification.long is not None  # this and action are hard to predict, so lets just check they are set
            assert notification.action is not None
            assert notification.classification == constants.NOTIFICATION_CLASSIFICATION_STATUS_CHANGE

            assoc_editor_template = re.escape(templates.EMAIL_NOTIFICATION)
            assoc_editor_to = re.escape('associate@example.com')
            assoc_editor_subject = re.escape(self.svc.short_notification(
                ApplicationAssedInprogressNotify.ID).replace("{issns}", ", ".join(issn for issn in
                                                                                  processor.source.bibjson().issns())) + "\n")  # "an application assigned to you has not passed review."
            assoc_editor_email_matched = re.search(
                email_log_regex % (assoc_editor_template, assoc_editor_to, assoc_editor_subject),
                info_stream_contents,
                re.DOTALL)
            assert bool(assoc_editor_email_matched)
            assert len(re.findall(email_count_string, info_stream_contents)) == 2

            # Clear the stream for the next part
            self.info_stream.truncate(0)

            # When an application is assigned to an associate editor for the first time, email the assoc_ed and publisher.

            # Refresh the application form
            no_ed = models.Suggestion(**deepcopy(ready_application.data))
            del no_ed['admin']['editor']
            fc = ApplicationFormFactory.context("admin")
            processor = fc.processor(source=no_ed)
            # fc = formcontext.ApplicationFormFactory.get_form_context(role="admin", source=no_ed)

            # Assign the associate editor and save the form
            processor.form.editor.data = "associate_3"

            processor.finalise(acc)

            info_stream_contents = self.info_stream.getvalue()

            # check the associate was changed
            assert processor.target.editor == "associate_3"

            # We expect 2 emails to be sent:
            #   * to the AssEd who's been assigned,
            #   * and to the publisher informing them there's an editor assigned.
            assEd_template = templates.EMAIL_NOTIFICATION
            assEd_to = re.escape(models.Account.pull('associate_3').email)
            assEd_subject = re.escape('New application ({}) assigned to you'.format(
                ', '.join(issn for issn in processor.source.bibjson().issns())))

            assEd_email_matched = re.search(email_log_regex % (assEd_template, assEd_to, assEd_subject),
                                            info_stream_contents,
                                            re.DOTALL)
            assert bool(assEd_email_matched), info_stream_contents.strip('\x00')
            assert len(re.findall(email_count_string, info_stream_contents)) == 1

            # Clear the stream for the next part
            self.info_stream.truncate(0)

            # Refresh the application form
            fc = ApplicationFormFactory.context("admin")
            processor = fc.processor(source=ready_application)
            # fc = formcontext.ApplicationFormFactory.get_form_context(role="admin", source=ready_application)

            # Next, if we change the editor group or assigned editor, emails should be sent to editors, & NOT the publisher
            processor.form.editor_group.data = "Test Editor Group"
            processor.form.editor.data = "associate_3"

            processor.finalise(acc)
            info_stream_contents = self.info_stream.getvalue()

            # check the associate was changed
            assert processor.target.editor == "associate_3"

            # We expect 2 emails to be sent:
            #   * to the managing editor of the assigned group,
            #   * to the AssEd who's been assigned
            editor_template = re.escape(templates.EMAIL_NOTIFICATION)
            editor_to = re.escape('maned@example.com')
            editor_subject = re.escape('New update request ({}) assigned to you'.format(
                ', '.join(issn for issn in processor.source.bibjson().issns())))

            editor_email_matched = re.search(email_log_regex % (editor_template, editor_to, editor_subject),
                                             info_stream_contents,
                                             re.DOTALL)
            assert bool(editor_email_matched)

            assEd_template = templates.EMAIL_NOTIFICATION
            assEd_to = re.escape(models.Account.pull('associate_3').email)
            assEd_subject = re.escape('New application ({}) assigned to you'.format(
                ', '.join(issn for issn in processor.source.bibjson().issns())))

            assEd_email_matched = re.search(email_log_regex % (assEd_template, assEd_to, assEd_subject),
                                            info_stream_contents,
                                            re.DOTALL)
            assert bool(assEd_email_matched), info_stream_contents.strip('\x00')
            assert len(re.findall(email_count_string, info_stream_contents)) == 2

            # Clear the stream for the next part
            self.info_stream.truncate(0)

            # A Managing Editor will notify other ManEds when they set an application to 'Ready'
            # Refresh the application form
            pending_application = models.Suggestion(**UPDATE_REQUEST_SOURCE_TEST_2)
            fc = ApplicationFormFactory.context("admin")
            processor = fc.processor(source=pending_application)
            # fc = formcontext.ApplicationFormFactory.get_form_context(role="admin", source=pending_application)

            # Make changes to the application status via the form
            processor.form.application_status.data = constants.APPLICATION_STATUS_READY

            processor.finalise(acc)
            info_stream_contents = self.info_stream.getvalue()

            # We expect one email to be sent here:
            #   * to the ManEds, saying an application is ready
            manEd_template = templates.EMAIL_NOTIFICATION
            manEd_to = re.escape("maned@example.com")
            manEd_subject = re.escape('Application ({}) marked as ready'.format(
                ', '.join(issn for issn in processor.source.bibjson().issns())))

            manEd_email_matched = re.search(email_log_regex % (manEd_template, manEd_to, manEd_subject),
                                            info_stream_contents,
                                            re.DOTALL)
            assert bool(manEd_email_matched)
            assert len(re.findall(email_count_string, info_stream_contents)) == 1

            # Clear the stream for the next part
            self.info_stream.truncate(0)

            # Finally, a Managing Editor will also trigger emails to the publisher when they accept an Application

            # Refresh the application form
            fc = ApplicationFormFactory.context("admin")
            processor = fc.processor(source=ready_application)
            # fc = formcontext.ApplicationFormFactory.get_form_context(role="admin", source=ready_application)
            processor.form.application_status.data = constants.APPLICATION_STATUS_ACCEPTED

            processor.finalise(acc)
            info_stream_contents = self.info_stream.getvalue()

            # We expect 3 email to be sent:
            #   * to the publisher, informing them of the journal's acceptance
            #   * to the journal contact, informing them of the journal's acceptance
            publisher_template = templates.EMAIL_NOTIFICATION
            publisher_to = re.escape(owner.email)
            publisher_subject = re.escape(
                'Update request ({}) accepted'.format(', '.join(issn for issn in processor.source.bibjson().issns())))

            publisher_email_matched = re.search(email_log_regex % (publisher_template, publisher_to, publisher_subject),
                                                info_stream_contents,
                                                re.DOTALL)
            assert bool(publisher_email_matched), (publisher_email_matched, info_stream_contents)
            assert len(re.findall(email_count_string, info_stream_contents)) == 3   # it's 3, we need a better way of testing these

    def test_02_ed_review_emails(self):
        """ Ensure the Editor's application review form sends the right emails"""
        acc = models.Account()
        acc.set_id("contextuser")
        acc.add_role("editor")
        with self._make_and_push_test_context_manager(acc=acc):
            # ctx = self._make_and_push_test_context(acc=acc)

            # If an application has been set to 'ready' from another status, the ManEds are notified
            pending_application = models.Suggestion(**UPDATE_REQUEST_SOURCE_TEST_2)

            owner = models.Account()
            owner.set_id(pending_application.owner)
            owner.set_name("Test Name")
            owner.set_email("test@example.com")
            owner.save(blocking=True)

            maned = models.Account()
            maned.set_id(EDITOR_GROUP_SOURCE.get("maned"))
            maned.set_email("maned@example.com")
            maned.save(blocking=True)

            # Construct an application form
            fc = ApplicationFormFactory.context("editor")
            processor = fc.processor(source=pending_application)
            # fc = formcontext.ApplicationFormFactory.get_form_context(
            #     role="editor",
            #     source=pending_application
            # )
            # assert isinstance(fc, formcontext.EditorApplicationReview)

            # Make changes to the application status via the form
            processor.form.application_status.data = constants.APPLICATION_STATUS_READY

            processor.finalise()
            info_stream_contents = self.info_stream.getvalue()

            # We expect one email to be sent here:
            #   * to the ManEds, saying an application is ready
            manEd_template = templates.EMAIL_NOTIFICATION
            manEd_to = re.escape("maned@example.com")
            manEd_subject = re.escape('Application ({}) marked as ready'.format(
                ', '.join(issn for issn in processor.source.bibjson().issns())))

            manEd_email_matched = re.search(email_log_regex % (manEd_template, manEd_to, manEd_subject),
                                            info_stream_contents,
                                            re.DOTALL)
            assert bool(manEd_email_matched)
            assert len(re.findall(email_count_string, info_stream_contents)) == 1

            # Clear the stream for the next part
            self.info_stream.truncate(0)

            # When an application is assigned to an associate editor for the first time, email the assoc_ed and publisher.

            # Refresh the application form
            no_ed = models.Suggestion(**deepcopy(pending_application.data))
            del no_ed['admin']['editor']
            fc = ApplicationFormFactory.context("editor")
            processor = fc.processor(source=no_ed)
            # fc = formcontext.ApplicationFormFactory.get_form_context(role="admin", source=no_ed)

            # Assign the associate editor and save the form
            processor.form.editor.data = "associate_3"

            processor.finalise()
            info_stream_contents = self.info_stream.getvalue()

            # check the associate was changed
            assert processor.target.editor == "associate_3"

            # We expect 2 emails to be sent:
            #   * to the AssEd who's been assigned,
            #   * and to the publisher informing them there's an editor assigned.
            assEd_template = templates.EMAIL_NOTIFICATION
            assEd_to = re.escape(models.Account.pull('associate_3').email)
            assEd_subject = re.escape('New application ({}) assigned to you'.format(
                ', '.join(issn for issn in processor.source.bibjson().issns())))

            assEd_email_matched = re.search(email_log_regex % (assEd_template, assEd_to, assEd_subject),
                                            info_stream_contents,
                                            re.DOTALL)
            assert bool(assEd_email_matched), info_stream_contents.strip('\x00')
            assert len(re.findall(email_count_string, info_stream_contents)) == 1

            # Clear the stream for the next part
            self.info_stream.truncate(0)

            # Editors can also reassign applications to different associate editors.
            fc = ApplicationFormFactory.context("editor")
            processor = fc.processor(source=models.Suggestion(**UPDATE_REQUEST_SOURCE_TEST_2))
            # fc = formcontext.ApplicationFormFactory.get_form_context(role="editor", source=models.Suggestion(**UPDATE_REQUEST_SOURCE_TEST_2))
            # assert isinstance(fc, formcontext.EditorApplicationReview)

            processor.form.editor.data = "associate_2"

            processor.finalise()
            info_stream_contents = self.info_stream.getvalue()

            # check the associate was changed
            assert processor.target.editor == "associate_2"

            # We expect 1 email to be sent:
            #   * to the AssEd who's been assigned,
            assEd_template = templates.EMAIL_NOTIFICATION
            assEd_to = re.escape(models.Account.pull('associate_2').email)
            assEd_subject = re.escape('New application ({}) assigned to you'.format(
                ', '.join(issn for issn in processor.source.bibjson().issns())))

            assEd_email_matched = re.search(email_log_regex % (assEd_template, assEd_to, assEd_subject),
                                            info_stream_contents,
                                            re.DOTALL)
            assert bool(assEd_email_matched), info_stream_contents.strip('\x00')
            assert len(re.findall(email_count_string, info_stream_contents)) == 1

            # Clear the stream for the next part
            self.info_stream.truncate(0)

            # When an editor changes the state from 'completed' to 'in progress', the assigned associate is emailed.
            completed_application = models.Suggestion(**UPDATE_REQUEST_SOURCE_TEST_2)
            completed_application.set_application_status(constants.APPLICATION_STATUS_COMPLETED)

            # Construct an application form
            fc = ApplicationFormFactory.context("editor")
            processor = fc.processor(source=completed_application)
            # fc = formcontext.ApplicationFormFactory.get_form_context(
            #     role="editor",
            #     source=completed_application
            # )
            # assert isinstance(fc, formcontext.EditorApplicationReview)

            # Make changes to the application status via the form
            processor.form.application_status.data = constants.APPLICATION_STATUS_IN_PROGRESS

            # Emails are sent during the finalise stage, and requires the app context to build URLs
            processor.finalise()

            # Use the captured info stream to get email send logs
            info_stream_contents = self.info_stream.getvalue()

            # Prove we went from to and from the right statuses
            assert processor.source.application_status == constants.APPLICATION_STATUS_COMPLETED
            assert processor.target.application_status == constants.APPLICATION_STATUS_IN_PROGRESS

            # We expect one email to be sent:
            #   * to the associate editor, informing them the application has been bounced back to in progress.
            assoc_editor_template = re.escape(templates.EMAIL_NOTIFICATION)
            assoc_editor_to = re.escape('associate@example.com')
            assoc_editor_subject = re.escape('One of your applications ({}) has not passed review'.format(
                ', '.join(issn for issn in processor.source.bibjson().issns())))
            assoc_editor_email_matched = re.search(
                email_log_regex % (assoc_editor_template, assoc_editor_to, assoc_editor_subject),
                info_stream_contents,
                re.DOTALL)
            assert bool(assoc_editor_email_matched)
            assert len(re.findall(email_count_string, info_stream_contents)) == 2

    def test_03_assoc_ed_review_emails(self):
        """ Ensure the Associate Editor's application review form sends the right emails"""
        acc = models.Account()
        acc.set_id("contextuser")
        acc.add_role("associate_editor")
        with self._make_and_push_test_context_manager(acc=acc):
            # If an application has been set to 'in progress' from 'pending', the publisher is notified
            pending_application = models.Suggestion(**UPDATE_REQUEST_SOURCE_TEST_3)

            owner = models.Account()
            owner.set_id(pending_application.owner)
            owner.set_name("Test Name")
            owner.set_email("test@example.com")
            owner.save(blocking=True)

            # Construct an application form
            fc = ApplicationFormFactory.context("associate_editor")
            processor = fc.processor(source=pending_application)
            # fc = formcontext.ApplicationFormFactory.get_form_context(
            #     role="associate_editor",
            #     source=pending_application
            # )
            # assert isinstance(fc, formcontext.AssEdApplicationReview)

            # Make changes to the application status via the form
            processor.form.application_status.data = constants.APPLICATION_STATUS_IN_PROGRESS

            processor.finalise()
            info_stream_contents = self.info_stream.getvalue()

            # We expect no email to be sent
            assert len(re.findall(email_count_string, info_stream_contents)) == 0

            # Clear the stream for the next part
            self.info_stream.truncate(0)

            # When the application is then set to 'completed', the editor in charge of this group is informed
            processor.form.application_status.data = constants.APPLICATION_STATUS_COMPLETED

            processor.finalise()
            info_stream_contents = self.info_stream.getvalue()

            # We expect one email sent:
            #   * to the editor, informing them an application has been completed by an Associate Editor
            editor_template = re.escape(templates.EMAIL_NOTIFICATION)
            editor_to = re.escape('eddie@example.com')
            editor_subject = re.escape("Application ({}) marked as completed".format(
                ', '.join(issn for issn in processor.source.bibjson().issns())))
            editor_email_matched = re.search(email_log_regex % (editor_template, editor_to, editor_subject),
                                             info_stream_contents,
                                             re.DOTALL)
            assert bool(editor_email_matched)
            assert len(re.findall(email_count_string, info_stream_contents)) == 1


class TestJournalReviewEmails(DoajTestCase):

    def setUp(self):
        super(TestJournalReviewEmails, self).setUp()

        self.editor_group_pull_by_key = models.EditorGroup.pull_by_key
        self.editor_group_pull = models.EditorGroup.pull
        models.EditorGroup.pull_by_key = editor_group_pull_by_key
        models.EditorGroup.pull = editor_group_pull

        self.editor_account_pull = models.Account.pull
        models.Account.pull = editor_account_pull

        # Register a new log handler so we can inspect the info logs
        self.info_stream = StringIO()
        self.read_info = logging.StreamHandler(self.info_stream)
        self.read_info.setLevel(logging.INFO)
        self.app_test.logger.addHandler(self.read_info)

    def tearDown(self):
        super(TestJournalReviewEmails, self).tearDown()

        models.EditorGroup.pull_by_key = self.editor_group_pull_by_key
        models.EditorGroup.pull = self.editor_group_pull
        models.Account.pull = self.editor_account_pull

        # Blank the info_stream and remove the error handler from the app
        self.info_stream.truncate(0)
        self.app_test.logger.removeHandler(self.read_info)

    def test_01_maned_review_emails(self):
        """ Ensure the Managing Editor's journal review form sends the right emails"""
        acc = models.Account()
        acc.set_id("contextuser")
        acc.add_role("admin")
        with self._make_and_push_test_context_manager(acc=acc):
            journal = models.Journal(**JOURNAL_SOURCE_TEST_1)

            # Construct a journal form
            fc = JournalFormFactory.context("admin")
            processor = fc.processor(source=journal)

            # If we change the editor group or assigned editor, emails should be sent to editors
            processor.form.editor_group.data = "Test Editor Group"
            processor.form.editor.data = "associate_3"

            processor.finalise()
            info_stream_contents = self.info_stream.getvalue()

            # check the associate was changed
            assert processor.target.editor == "associate_3"

            # We expect no emails to be sent
            assert len(re.findall(email_count_string, info_stream_contents)) == 0

    def test_02_ed_review_emails(self):
        """ Ensure the Editor's journal review form sends the right emails"""
        acc = models.Account()
        acc.set_id("contextuser")
        acc.add_role("editor")
        with self._make_and_push_test_context_manager(acc=acc):
            # Editors can reassign journals to associate editors.
            fc = JournalFormFactory.context("editor")
            processor = fc.processor(source=models.Journal(**JOURNAL_SOURCE_TEST_2))
            processor.form.editor.data = "associate_2"

            processor.finalise()
            info_stream_contents = self.info_stream.getvalue()

            # check the associate was changed
            assert processor.target.editor == "associate_2"

            # We no email to be sent
            assert len(re.findall(email_count_string, info_stream_contents)) == 0

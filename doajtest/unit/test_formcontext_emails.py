import logging
import re
from StringIO import StringIO
from copy import deepcopy

from portality import constants
from doajtest.fixtures import EditorGroupFixtureFactory, AccountFixtureFactory, ApplicationFixtureFactory, JournalFixtureFactory
from doajtest.helpers import DoajTestCase
from portality import models
from portality.formcontext import formcontext

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
    else:
        return ACTUAL_ACCOUNT_PULL(_id)

ACTUAL_ACCOUNT_PULL = models.Account.pull

# A regex string for searching the log entries
email_log_regex = 'template.*%s.*to:\[u{0,1}\'%s.*subject:.*%s'

# A string present in each email log entry (for counting them)
email_count_string = 'Email template'


class TestPublicApplicationEmails(DoajTestCase):
    def setUp(self):
        super(TestPublicApplicationEmails, self).setUp()

        # Register a new log handler so we can inspect the info logs
        self.info_stream = StringIO()
        self.read_info = logging.StreamHandler(self.info_stream)
        self.read_info.setLevel(logging.INFO)
        self.app_test.logger.addHandler(self.read_info)

    def tearDown(self):
        super(TestPublicApplicationEmails, self).tearDown()

        # Blank the info_stream and remove the error handler from the app
        self.info_stream.truncate(0)
        self.app_test.logger.removeHandler(self.read_info)

    def test_01_public_application_email(self):
        application = models.Suggestion(**APPLICATION_SOURCE_TEST_1)

        # Construct an application form
        fc = formcontext.ApplicationFormFactory.get_form_context(
            role=None,
            source=application
        )
        assert isinstance(fc, formcontext.PublicApplication)

        # Emails are sent during the finalise stage, and requires the app context to build URLs
        with self.app_test.test_request_context():
            fc.finalise()
        # Use the captured info stream to get email send logs
        info_stream_contents = self.info_stream.getvalue()

        # We expect one email sent:
        #   * to the applicant, informing them the application was received
        public_template = re.escape('publisher_application_received.txt')
        public_to = re.escape('suggester@email.com')
        public_subject = "Directory of Open Access Journals - your application to DOAJ has been received"
        public_email_matched = re.search(email_log_regex % (public_template, public_to, public_subject),
                                         info_stream_contents,
                                         re.DOTALL)
        assert bool(public_email_matched)
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

    def tearDown(self):
        super(TestApplicationReviewEmails, self).tearDown()

        models.EditorGroup.pull_by_key = self.editor_group_pull_by_key
        models.EditorGroup.pull = self.editor_group_pull
        models.Account.pull = self.editor_account_pull

        # Blank the info_stream and remove the error handler from the app
        self.info_stream.truncate(0)
        self.app_test.logger.removeHandler(self.read_info)

    def test_01_maned_review_emails(self):
        """ Ensure the Managing Editor's application review form sends the right emails"""
        acc = models.Account()
        acc.set_id("contextuser")
        acc.add_role("admin")
        ctx = self._make_and_push_test_context(acc=acc)

        # If an application has been set to 'ready' but is returned to 'in progress',
        # an email is sent to the editor and assigned associate editor
        ready_application = models.Suggestion(**APPLICATION_SOURCE_TEST_1)
        ready_application.set_application_status(constants.APPLICATION_STATUS_READY)

        # Construct an application form
        fc = formcontext.ApplicationFormFactory.get_form_context(
            role="admin",
            source=ready_application
        )
        assert isinstance(fc, formcontext.ManEdApplicationReview)

        # Make changes to the application status via the form
        fc.form.application_status.data = constants.APPLICATION_STATUS_IN_PROGRESS

        # Emails are sent during the finalise stage, and requires the app context to build URLs
        fc.finalise()

        # Use the captured info stream to get email send logs
        info_stream_contents = self.info_stream.getvalue()

        # Prove we went from to and from the right statuses
        assert fc.source.application_status == constants.APPLICATION_STATUS_READY
        assert fc.target.application_status == constants.APPLICATION_STATUS_IN_PROGRESS

        # We expect two emails sent:
        #   * to the editor, informing them an application has been bounced from ready back to in progress.
        #   * to the associate editor, informing them the same
        editor_template = re.escape('editor_application_inprogress.txt')
        editor_to = re.escape('eddie@example.com')
        editor_subject = "Application reverted to 'In Progress' by Managing Editor"
        editor_email_matched = re.search(email_log_regex % (editor_template, editor_to, editor_subject),
                                         info_stream_contents,
                                         re.DOTALL)
        assert bool(editor_email_matched)

        assoc_editor_template = re.escape('assoc_editor_application_inprogress.txt')
        assoc_editor_to = re.escape('associate@example.com')
        assoc_editor_subject = "an application assigned to you has not passed review."
        assoc_editor_email_matched = re.search(email_log_regex % (assoc_editor_template, assoc_editor_to, assoc_editor_subject),
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
        fc = formcontext.ApplicationFormFactory.get_form_context(
            role="admin",
            source=completed_application
        )
        assert isinstance(fc, formcontext.ManEdApplicationReview)

        # Make changes to the application status via the form
        fc.form.application_status.data = constants.APPLICATION_STATUS_IN_PROGRESS

        # Emails are sent during the finalise stage, and requires the app context to build URLs
        fc.finalise()

        # Use the captured info stream to get email send logs
        info_stream_contents = self.info_stream.getvalue()

        # Prove we went from to and from the right statuses
        assert fc.source.application_status == constants.APPLICATION_STATUS_COMPLETED
        assert fc.target.application_status == constants.APPLICATION_STATUS_IN_PROGRESS

        # We expect two emails sent:
        #   * to the editor, informing them an application has been bounced from completed back to in progress.
        #   * to the associate editor, informing them the same
        editor_template = re.escape('editor_application_inprogress.txt')
        editor_to = re.escape('eddie@example.com')
        editor_subject = "Application reverted to 'In Progress' by Managing Editor"
        editor_email_matched = re.search(email_log_regex % (editor_template, editor_to, editor_subject),
                                         info_stream_contents,
                                         re.DOTALL)
        assert bool(editor_email_matched)

        assoc_editor_template = re.escape('assoc_editor_application_inprogress.txt')
        assoc_editor_to = re.escape('associate@example.com')
        assoc_editor_subject = "an application assigned to you has not passed review."
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
        no_ed = deepcopy(ready_application)
        del no_ed['admin']['editor']
        fc = formcontext.ApplicationFormFactory.get_form_context(role="admin", source=no_ed)

        # Assign the associate editor and save the form
        fc.form.editor.data = "associate_3"

        fc.finalise()
        info_stream_contents = self.info_stream.getvalue()

        # check the associate was changed
        assert fc.target.editor == "associate_3"

        # We expect 2 emails to be sent:
        #   * to the AssEd who's been assigned,
        #   * and to the publisher informing them there's an editor assigned.
        assEd_template = 'assoc_editor_application_assigned.txt'
        assEd_to = re.escape(models.Account.pull('associate_3').email)
        assEd_subject = 'new application assigned to you'

        assEd_email_matched = re.search(email_log_regex % (assEd_template, assEd_to, assEd_subject),
                                        info_stream_contents,
                                        re.DOTALL)
        assert bool(assEd_email_matched)

        publisher_template = 'publisher_application_editor_assigned.txt'
        publisher_to = re.escape(no_ed.get_latest_contact_email())
        publisher_subject = 'your application has been assigned an editor for review'

        publisher_email_matched = re.search(email_log_regex % (publisher_template, publisher_to, publisher_subject),
                                            info_stream_contents,
                                            re.DOTALL)
        assert bool(publisher_email_matched)
        assert len(re.findall(email_count_string, info_stream_contents)) == 2

        # Clear the stream for the next part
        self.info_stream.truncate(0)

        # Refresh the application form
        fc = formcontext.ApplicationFormFactory.get_form_context(role="admin", source=ready_application)

        # Next, if we change the editor group or assigned editor, emails should be sent to editors, & NOT the publisher
        fc.form.editor_group.data = "Test Editor Group"
        fc.form.editor.data = "associate_3"

        fc.finalise()
        info_stream_contents = self.info_stream.getvalue()

        # check the associate was changed
        assert fc.target.editor == "associate_3"

        # We expect 2 emails to be sent:
        #   * to the editor of the assigned group,
        #   * to the AssEd who's been assigned
        editor_template = re.escape('editor_application_assigned_group.txt')
        editor_to = re.escape('eddie@example.com')
        editor_subject = 'new application assigned to your group'

        editor_email_matched = re.search(email_log_regex % (editor_template, editor_to, editor_subject),
                                         info_stream_contents,
                                         re.DOTALL)
        assert bool(editor_email_matched)

        assEd_template = 'assoc_editor_application_assigned.txt'
        assEd_to = re.escape(models.Account.pull('associate_3').email)
        assEd_subject = 'new application assigned to you'

        assEd_email_matched = re.search(email_log_regex % (assEd_template, assEd_to, assEd_subject),
                                        info_stream_contents,
                                        re.DOTALL)
        assert bool(assEd_email_matched)
        assert len(re.findall(email_count_string, info_stream_contents)) == 2

        # Clear the stream for the next part
        self.info_stream.truncate(0)

        # A Managing Editor will notify other ManEds when they set an application to 'Ready'
        # Refresh the application form
        pending_application = models.Suggestion(**APPLICATION_SOURCE_TEST_2)
        fc = formcontext.ApplicationFormFactory.get_form_context(role="admin", source=pending_application)

        # Make changes to the application status via the form
        fc.form.application_status.data = constants.APPLICATION_STATUS_READY

        fc.finalise()
        info_stream_contents = self.info_stream.getvalue()

        # We expect one email to be sent here:
        #   * to the ManEds, saying an application is ready
        manEd_template = 'admin_application_ready.txt'
        manEd_to = re.escape(self.app_test.config.get('MANAGING_EDITOR_EMAIL'))
        manEd_subject = 'application ready'

        manEd_email_matched = re.search(email_log_regex % (manEd_template, manEd_to, manEd_subject),
                                        info_stream_contents,
                                        re.DOTALL)
        assert bool(manEd_email_matched)
        assert len(re.findall(email_count_string, info_stream_contents)) == 1

        # Clear the stream for the next part
        self.info_stream.truncate(0)

        # Finally, a Managing Editor will also trigger emails to the publisher when they accept an Application

        # Refresh the application form
        fc = formcontext.ApplicationFormFactory.get_form_context(role="admin", source=ready_application)
        fc.form.application_status.data = constants.APPLICATION_STATUS_ACCEPTED

        fc.finalise()
        info_stream_contents = self.info_stream.getvalue()

        # We expect 3 emails to be sent:
        #   * to the publisher, because they have a new account
        #   * to the publisher, informing them of the journal's acceptance
        #   * to the journal contact, informing them of the journal's acceptance
        publisher_template = 'account_created.txt'
        publisher_to = re.escape(ready_application.get_latest_contact_email())
        publisher_subject = 'account created'

        publisher_email_matched = re.search(email_log_regex % (publisher_template, publisher_to, publisher_subject),
                                            info_stream_contents,
                                            re.DOTALL)
        assert bool(publisher_email_matched)

        publisher_template = 'publisher_update_request_accepted.txt'
        publisher_to = re.escape(ready_application.get_latest_contact_email())
        publisher_subject = 'journal accepted'

        publisher_email_matched = re.search(email_log_regex % (publisher_template, publisher_to, publisher_subject),
                                            info_stream_contents,
                                            re.DOTALL)
        assert bool(publisher_email_matched), (publisher_email_matched, info_stream_contents)

        """
        # Current setup means that this third email is no longer sent.  Keeping this code for the
        # moment, as a review of email sending is probably necessary
        publisher_template = 'contact_update_request_accepted.txt'
        publisher_to = re.escape(ready_application.get_latest_contact_email())
        publisher_subject = 'journal accepted'

        print(email_log_regex)
        print(publisher_to)
        print (info_stream_contents)

        publisher_email_matched = re.search(email_log_regex % (publisher_template, publisher_to, publisher_subject),
                                            info_stream_contents,
                                            re.DOTALL)
        assert bool(publisher_email_matched)
        """

        assert len(re.findall(email_count_string, info_stream_contents)) == 2

        ctx.pop()

    def test_02_ed_review_emails(self):
        """ Ensure the Editor's application review form sends the right emails"""
        acc = models.Account()
        acc.set_id("contextuser")
        acc.add_role("editor")
        ctx = self._make_and_push_test_context(acc=acc)

        # If an application has been set to 'ready' from another status, the ManEds are notified
        pending_application = models.Suggestion(**APPLICATION_SOURCE_TEST_2)

        # Construct an application form
        fc = formcontext.ApplicationFormFactory.get_form_context(
            role="editor",
            source=pending_application
        )
        assert isinstance(fc, formcontext.EditorApplicationReview)

        # Make changes to the application status via the form
        fc.form.application_status.data = constants.APPLICATION_STATUS_READY

        fc.finalise()
        info_stream_contents = self.info_stream.getvalue()

        # We expect one email to be sent here:
        #   * to the ManEds, saying an application is ready
        manEd_template = 'admin_application_ready.txt'
        manEd_to = re.escape(self.app_test.config.get('MANAGING_EDITOR_EMAIL'))
        manEd_subject = 'application ready'

        manEd_email_matched = re.search(email_log_regex % (manEd_template, manEd_to, manEd_subject),
                                        info_stream_contents,
                                        re.DOTALL)
        assert bool(manEd_email_matched)
        assert len(re.findall(email_count_string, info_stream_contents)) == 1

        # Clear the stream for the next part
        self.info_stream.truncate(0)

        # When an application is assigned to an associate editor for the first time, email the assoc_ed and publisher.

        # Refresh the application form
        no_ed = deepcopy(pending_application)
        del no_ed['admin']['editor']
        fc = formcontext.ApplicationFormFactory.get_form_context(role="admin", source=no_ed)

        # Assign the associate editor and save the form
        fc.form.editor.data = "associate_3"

        fc.finalise()
        info_stream_contents = self.info_stream.getvalue()

        # check the associate was changed
        assert fc.target.editor == "associate_3"

        # We expect 2 emails to be sent:
        #   * to the AssEd who's been assigned,
        #   * and to the publisher informing them there's an editor assigned.
        assEd_template = 'assoc_editor_application_assigned.txt'
        assEd_to = re.escape(models.Account.pull('associate_3').email)
        assEd_subject = 'new application assigned to you'

        assEd_email_matched = re.search(email_log_regex % (assEd_template, assEd_to, assEd_subject),
                                        info_stream_contents,
                                        re.DOTALL)
        assert bool(assEd_email_matched)

        publisher_template = 'publisher_application_editor_assigned.txt'
        publisher_to = re.escape(no_ed.get_latest_contact_email())
        publisher_subject = 'your application has been assigned an editor for review'

        publisher_email_matched = re.search(email_log_regex % (publisher_template, publisher_to, publisher_subject),
                                            info_stream_contents,
                                            re.DOTALL)
        assert bool(publisher_email_matched)
        assert len(re.findall(email_count_string, info_stream_contents)) == 2

        # Clear the stream for the next part
        self.info_stream.truncate(0)

        # Editors can also reassign applications to different associate editors.
        fc = formcontext.ApplicationFormFactory.get_form_context(role="editor", source=models.Suggestion(**APPLICATION_SOURCE_TEST_2))
        assert isinstance(fc, formcontext.EditorApplicationReview)

        fc.form.editor.data = "associate_2"

        fc.finalise()
        info_stream_contents = self.info_stream.getvalue()

        # check the associate was changed
        assert fc.target.editor == "associate_2"

        # We expect 1 email to be sent:
        #   * to the AssEd who's been assigned,
        assEd_template = 'assoc_editor_application_assigned.txt'
        assEd_to = re.escape(models.Account.pull('associate_2').email)
        assEd_subject = 'new application assigned to you'

        assEd_email_matched = re.search(email_log_regex % (assEd_template, assEd_to, assEd_subject),
                                        info_stream_contents,
                                        re.DOTALL)
        assert bool(assEd_email_matched)
        assert len(re.findall(email_count_string, info_stream_contents)) == 1

        # Clear the stream for the next part
        self.info_stream.truncate(0)

        # When an editor changes the state from 'completed' to 'in progress', the assigned associate is emailed.
        completed_application = models.Suggestion(**APPLICATION_SOURCE_TEST_2)
        completed_application.set_application_status(constants.APPLICATION_STATUS_COMPLETED)

        # Construct an application form
        fc = formcontext.ApplicationFormFactory.get_form_context(
            role="editor",
            source=completed_application
        )
        assert isinstance(fc, formcontext.EditorApplicationReview)

        # Make changes to the application status via the form
        fc.form.application_status.data = constants.APPLICATION_STATUS_IN_PROGRESS

        # Emails are sent during the finalise stage, and requires the app context to build URLs
        fc.finalise()

        # Use the captured info stream to get email send logs
        info_stream_contents = self.info_stream.getvalue()

        # Prove we went from to and from the right statuses
        assert fc.source.application_status == constants.APPLICATION_STATUS_COMPLETED
        assert fc.target.application_status == constants.APPLICATION_STATUS_IN_PROGRESS

        # We expect one email to be sent:
        #   * to the associate editor, informing them the application has been bounced back to in progress.
        assoc_editor_template = re.escape('assoc_editor_application_inprogress.txt')
        assoc_editor_to = re.escape('associate@example.com')
        assoc_editor_subject = "an application assigned to you has not passed review."
        assoc_editor_email_matched = re.search(
            email_log_regex % (assoc_editor_template, assoc_editor_to, assoc_editor_subject),
            info_stream_contents,
            re.DOTALL)
        assert bool(assoc_editor_email_matched)

        assert len(re.findall(email_count_string, info_stream_contents)) == 1

        ctx.pop()

    def test_03_assoc_ed_review_emails(self):
        """ Ensure the Associate Editor's application review form sends the right emails"""
        acc = models.Account()
        acc.set_id("contextuser")
        acc.add_role("associate_editor")
        ctx = self._make_and_push_test_context(acc=acc)

        # If an application has been set to 'in progress' from 'pending', the publisher is notified
        pending_application = models.Suggestion(**APPLICATION_SOURCE_TEST_3)

        # Construct an application form
        fc = formcontext.ApplicationFormFactory.get_form_context(
            role="associate_editor",
            source=pending_application
        )
        assert isinstance(fc, formcontext.AssEdApplicationReview)

        # Make changes to the application status via the form
        fc.form.application_status.data = constants.APPLICATION_STATUS_IN_PROGRESS

        fc.finalise()
        info_stream_contents = self.info_stream.getvalue()

        # We expect one email to be sent here:
        #   * to the publisher, notifying that an editor is viewing their application
        publisher_template = re.escape('publisher_application_inprogress.txt')
        publisher_to = re.escape(pending_application.get_latest_contact_email())
        publisher_subject = 'your application is under review'

        publisher_email_matched = re.search(email_log_regex % (publisher_template, publisher_to, publisher_subject),
                                            info_stream_contents,
                                            re.DOTALL)
        assert bool(publisher_email_matched)
        assert len(re.findall(email_count_string, info_stream_contents)) == 1

        # Clear the stream for the next part
        self.info_stream.truncate(0)

        # When the application is then set to 'completed', the editor in charge of this group is informed
        fc.form.application_status.data = constants.APPLICATION_STATUS_COMPLETED

        fc.finalise()
        info_stream_contents = self.info_stream.getvalue()

        # We expect one email sent:
        #   * to the editor, informing them an application has been completed by an Associate Editor
        editor_template = re.escape('editor_application_completed.txt')
        editor_to = re.escape('eddie@example.com')
        editor_subject = "application marked 'completed'"
        editor_email_matched = re.search(email_log_regex % (editor_template, editor_to, editor_subject),
                                         info_stream_contents,
                                         re.DOTALL)
        assert bool(editor_email_matched)
        assert len(re.findall(email_count_string, info_stream_contents)) == 1

        ctx.pop()


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
        journal = models.Journal(**JOURNAL_SOURCE_TEST_1)

        # Construct an journal form
        fc = formcontext.JournalFormFactory.get_form_context(
            role="admin",
            source=journal
        )
        assert isinstance(fc, formcontext.ManEdJournalReview)

        # If we change the editor group or assigned editor, emails should be sent to editors
        fc.form.editor_group.data = "Test Editor Group"
        fc.form.editor.data = "associate_3"

        with self.app_test.test_request_context():
            fc.finalise()
        info_stream_contents = self.info_stream.getvalue()

        # check the associate was changed
        assert fc.target.editor == "associate_3"

        # We expect 2 emails to be sent:
        #   * to the editor of the assigned group,
        #   * to the AssEd who's been assigned,
        editor_template = re.escape('editor_journal_assigned_group.txt')
        editor_to = re.escape('eddie@example.com')
        editor_subject = 'new journal assigned to your group'

        editor_email_matched = re.search(email_log_regex % (editor_template, editor_to, editor_subject),
                                         info_stream_contents,
                                         re.DOTALL)
        assert bool(editor_email_matched)

        assEd_template = 'assoc_editor_journal_assigned.txt'
        assEd_to = re.escape(models.Account.pull('associate_3').email)
        assEd_subject = 'new journal assigned to you'

        assEd_email_matched = re.search(email_log_regex % (assEd_template, assEd_to, assEd_subject),
                                        info_stream_contents,
                                        re.DOTALL)
        assert bool(assEd_email_matched)
        assert len(re.findall(email_count_string, info_stream_contents)) == 2

    def test_02_ed_review_emails(self):
        """ Ensure the Editor's journal review form sends the right emails"""
        journal = models.Journal(**JOURNAL_SOURCE_TEST_2)

        # Construct an journal form
        fc = formcontext.JournalFormFactory.get_form_context(
            role="editor",
            source=journal
        )
        assert isinstance(fc, formcontext.EditorJournalReview)

        # Editors can reassign journals to associate editors.
        fc = formcontext.JournalFormFactory.get_form_context(role="editor", source=models.Journal(**JOURNAL_SOURCE_TEST_2))
        assert isinstance(fc, formcontext.EditorJournalReview)

        fc.form.editor.data = "associate_2"

        with self.app_test.test_request_context():
            fc.finalise()
        info_stream_contents = self.info_stream.getvalue()

        # check the associate was changed
        assert fc.target.editor == "associate_2"

        # We expect 1 email to be sent:
        #   * to the AssEd who's been assigned
        assEd_template = 'assoc_editor_journal_assigned.txt'
        assEd_to = re.escape(models.Account.pull('associate_2').email)
        assEd_subject = 'new journal assigned to you'

        assEd_email_matched = re.search(email_log_regex % (assEd_template, assEd_to, assEd_subject),
                                        info_stream_contents,
                                        re.DOTALL)
        assert bool(assEd_email_matched)
        assert len(re.findall(email_count_string, info_stream_contents)) == 1

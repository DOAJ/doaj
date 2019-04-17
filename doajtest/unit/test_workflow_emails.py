from datetime import datetime, timedelta

from nose.tools import assert_raises, assert_false

from portality import constants
from doajtest.fixtures import EditorGroupFixtureFactory, AccountFixtureFactory, ApplicationFixtureFactory, JournalFixtureFactory
from doajtest.helpers import DoajTestCase
from portality import models
from portality.background import BackgroundException
from portality.core import app
from portality.tasks import async_workflow_notifications

APPLICATION_SOURCE = ApplicationFixtureFactory.make_application_source()

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


class TestAsyncWorkflowEmails(DoajTestCase):

    def setUp(self):
        super(TestAsyncWorkflowEmails, self).setUp()

        self.editor_group_pull_by_key = models.EditorGroup.pull_by_key
        self.editor_group_pull = models.EditorGroup.pull
        models.EditorGroup.pull_by_key = editor_group_pull_by_key
        models.EditorGroup.pull = editor_group_pull

        self.editor_account_pull = models.Account.pull
        models.Account.pull = editor_account_pull

    def tearDown(self):
        super(TestAsyncWorkflowEmails, self).tearDown()

        models.EditorGroup.pull_by_key = self.editor_group_pull_by_key
        models.EditorGroup.pull = self.editor_group_pull
        models.Account.pull = self.editor_account_pull

    def test_01_workflow_email_background_task_prepare(self):
        """ Job preparation should not succeed when emails are disabled in config """

        user = app.config.get("SYSTEM_USERNAME", 'test_system')
        app.config['ENABLE_EMAIL'] = False
        assert_raises(BackgroundException, async_workflow_notifications.AsyncWorkflowBackgroundTask.prepare, username=user)

        # Should succeed when enabled
        app.config['ENABLE_EMAIL'] = True
        job = async_workflow_notifications.AsyncWorkflowBackgroundTask.prepare(user)

    def test_02_workflow_managing_editor_notifications(self):
        ctx = self._make_and_push_test_context()

        emails = {}

        # When we make the application unchanged for a short period of time, we don't tell the managing editors
        [APPLICATION_SOURCE_1, APPLICATION_SOURCE_2, APPLICATION_SOURCE_3] = ApplicationFixtureFactory.make_many_application_sources(count=3)
        comfortably_idle = app.config['ASSOC_ED_IDLE_DAYS'] + 1
        APPLICATION_SOURCE_1['last_manual_update'] = datetime.utcnow() - timedelta(days=comfortably_idle)
        application1 = models.Suggestion(**APPLICATION_SOURCE_1)
        application1.save()

        # This exceeds the idle limit, managing editors should be notified.
        APPLICATION_SOURCE_2['admin']['application_status'] = constants.APPLICATION_STATUS_IN_PROGRESS
        extremely_idle = app.config['MAN_ED_IDLE_WEEKS'] + 1
        APPLICATION_SOURCE_2['last_manual_update'] = datetime.utcnow() - timedelta(weeks=extremely_idle)
        application2 = models.Suggestion(**APPLICATION_SOURCE_2)
        application2.save()

        # This one is ready - managing editors are told as it's now their responsibility.
        APPLICATION_SOURCE_3['last_manual_update'] = datetime.utcnow()
        APPLICATION_SOURCE_3['admin']['application_status'] = constants.APPLICATION_STATUS_READY
        application3 = models.Suggestion(**APPLICATION_SOURCE_3)
        application3.save()

        models.Suggestion.blockall([
            (application1.id, application1.last_updated),
            (application2.id, application2.last_updated),
            (application3.id, application3.last_updated)
        ])

        async_workflow_notifications.managing_editor_notifications(emails)
        assert len(emails) > 0
        assert app.config['MANAGING_EDITOR_EMAIL'] in emails.keys()

        email_text_catted = " ".join(emails[app.config['MANAGING_EDITOR_EMAIL']][1])
        assert u'1 application(s) are assigned to an Associate Editor' in email_text_catted
        assert u"There are 1 records in status 'Ready'" in email_text_catted
        ctx.pop()

    def test_03_workflow_editor_notifications(self):
        ctx = self._make_and_push_test_context()

        emails = {}

        # When we make the application unchanged for a short period of time, we don't tell the editors
        [APPLICATION_SOURCE_1, APPLICATION_SOURCE_2, APPLICATION_SOURCE_3] = ApplicationFixtureFactory.make_many_application_sources(count=3)
        comfortably_idle = app.config['ASSOC_ED_IDLE_DAYS'] + 1
        APPLICATION_SOURCE_1['last_manual_update'] = datetime.utcnow() - timedelta(days=comfortably_idle)
        application1 = models.Suggestion(**APPLICATION_SOURCE_1)
        application1.save()

        # This exceeds the idle limit, editors should be notified.
        APPLICATION_SOURCE_2['admin']['application_status'] = constants.APPLICATION_STATUS_IN_PROGRESS
        extremely_idle = app.config['ED_IDLE_WEEKS'] + 1
        APPLICATION_SOURCE_2['last_manual_update'] = datetime.utcnow() - timedelta(weeks=extremely_idle)
        application2 = models.Suggestion(**APPLICATION_SOURCE_2)
        application2.save()

        # This one is assigned to the group but not an associate - editors are reminded.
        extremely_idle = app.config['ED_IDLE_WEEKS'] + 1
        APPLICATION_SOURCE_2['admin']['application_status'] = constants.APPLICATION_STATUS_UPDATE_REQUEST
        APPLICATION_SOURCE_3['last_manual_update'] = datetime.utcnow() - timedelta(days=extremely_idle)
        APPLICATION_SOURCE_3['admin']['editor'] = None
        application3 = models.Suggestion(**APPLICATION_SOURCE_3)
        application3.save()

        models.Suggestion.blockall([
            (application1.id, application1.last_updated),
            (application2.id, application2.last_updated),
            (application3.id, application3.last_updated)
        ])

        async_workflow_notifications.editor_notifications(emails)

        assert len(emails) > 0
        assert EDITOR_SOURCE['email'] in emails.keys()

        email_text_catted = " ".join(emails[EDITOR_SOURCE['email']][1])
        assert u'1 application(s) currently assigned to your Editor Group, "editorgroup", which have no Associate Editor' in email_text_catted
        assert u"1 application(s) which have been assigned to an Associate Editor but have been idle" in email_text_catted

        ctx.pop()

    def test_04_workflow_associate_editor_notifications(self):
        ctx = self._make_and_push_test_context()

        APPLICATION_SOURCE['last_manual_update'] = datetime.utcnow()
        application = models.Suggestion(**APPLICATION_SOURCE)
        application.save(blocking=True)

        # This application is assigned to associate editor 1, but it is not yet stale enough to require a reminder
        emails = {}
        async_workflow_notifications.associate_editor_notifications(emails)
        assert_false(emails)

        # When we make the application unchanged for a period of time, we expect a message to be generated
        [APPLICATION_SOURCE_2, APPLICATION_SOURCE_3] = ApplicationFixtureFactory.make_many_application_sources(count=2)
        comfortably_idle = app.config['ASSOC_ED_IDLE_DAYS'] + 1
        APPLICATION_SOURCE_2['last_manual_update'] = datetime.utcnow() - timedelta(days=comfortably_idle)
        application2 = models.Suggestion(**APPLICATION_SOURCE_2)
        application2.save()

        extremely_idle = app.config['ASSOC_ED_IDLE_WEEKS'] + 1
        APPLICATION_SOURCE_3['last_manual_update'] = datetime.utcnow() - timedelta(weeks=extremely_idle)
        application3 = models.Suggestion(**APPLICATION_SOURCE_3)
        application3.save()

        models.Suggestion.blockall([
            (application.id, application.last_updated),
            (application2.id, application2.last_updated),
            (application3.id, application3.last_updated)
        ])

        async_workflow_notifications.associate_editor_notifications(emails)
        assert len(emails) > 0
        assert ASSED1_SOURCE['email'] in emails.keys()

        email_text = emails[ASSED1_SOURCE['email']][1].pop()
        assert u'You have 2 application(s) assigned to you' in email_text
        assert u'including 1 which have been unchanged' in email_text

        ctx.pop()

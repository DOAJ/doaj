from doajtest.fixtures import JournalFixtureFactory
from doajtest.helpers import DoajTestCase
from portality import models, constants

from doajtest.helpers import DoajTestCase
from portality.forms.application_forms import ApplicationFormFactory

from doajtest.fixtures.v2.applications import ApplicationFixtureFactory
from portality.ui.messages import Messages

APPLICATION_FORM = ApplicationFixtureFactory.make_application_form()


class TestPublicApplicationProcessor(DoajTestCase):

    def setUp(self):
        super(TestPublicApplicationProcessor, self).setUp()

    def tearDown(self):
        super(TestPublicApplicationProcessor, self).tearDown()

    def test_01_do_not_accept_nonexistant(self):
        application_source = ApplicationFixtureFactory.make_application_source()
        ready_application = models.Suggestion(**application_source)
        ready_application.save(blocking=True)
        formulaic_context = ApplicationFormFactory.context("admin")
        fc = formulaic_context.processor(source=ready_application)
        ready_application.delete()
        with self.assertRaises(Exception, msg=Messages.EXCEPTION_EDITING_NON_EXISTING_APPLICATION):
            fc.save()

    def test_02_do_not_accept_withdrawn(self):
        journal_source = JournalFixtureFactory.make_journal_source()
        journal = models.Journal(**journal_source)
        application_source = ApplicationFixtureFactory.make_application_source()
        ready_application = models.Suggestion(**application_source)
        ready_application.set_current_journal(journal.id)
        journal.set_in_doaj(False)
        journal.save(blocking=True)
        ready_application.set_application_status(constants.APPLICATION_STATUS_ACCEPTED)
        formulaic_context = ApplicationFormFactory.context("admin")
        fc = formulaic_context.processor(source=ready_application)
        with self.assertRaises(Exception, msg=Messages.EXCEPTION_EDITING_WITHDRAWN_JOURNAL):
            fc.save()

    def test_03_do_not_accept_deleted(self):
        journal_source = JournalFixtureFactory.make_journal_source()
        journal = models.Journal(**journal_source)
        application_source = ApplicationFixtureFactory.make_application_source()
        ready_application = models.Suggestion(**application_source)
        ready_application.set_current_journal(journal.id)
        # here journal is not saved - it doesn't exist
        ready_application.set_application_status(constants.APPLICATION_STATUS_ACCEPTED)
        formulaic_context = ApplicationFormFactory.context("admin")
        fc = formulaic_context.processor(source=ready_application)
        with self.assertRaises(Exception, msg=Messages.EXCEPTION_EDITING_DELETED_JOURNAL):
            fc.save()

    def test_04_do_not_edit_accepted(self):
        acc = models.Account.make_account(email='user@example.com', username='mrs_user',
                                          roles=['api', 'admin'])
        journal_source = JournalFixtureFactory.make_journal_source()
        journal = models.Journal(**journal_source)
        application_source = ApplicationFixtureFactory.make_application_source()
        ready_application = models.Suggestion(**application_source)
        ready_application.set_current_journal(journal.id)
        journal.save(blocking=True)
        ready_application.set_application_status(constants.APPLICATION_STATUS_ACCEPTED)
        formulaic_context = ApplicationFormFactory.context("admin")
        fc = formulaic_context.processor(source=ready_application)
        with self.assertRaises(Exception, msg=Messages.EXCEPTION_EDITING_ACCEPTED_JOURNAL):
            fc.finalise(acc)

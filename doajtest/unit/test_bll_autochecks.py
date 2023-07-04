import time

from doajtest.helpers import DoajTestCase
from portality import models
from portality.bll import DOAJ

from doajtest.fixtures import ApplicationFixtureFactory, JournalFixtureFactory
from doajtest.mocks.autocheck_resource_bundle_Resource import ResourceBundleResourceMockFactory
from doajtest.mocks.autocheck_checkers import AutocheckMockFactory

from portality.autocheck.resource_bundle import Resource


class TestBLLAutochecks(DoajTestCase):

    def setUp(self):
        mock_fetch = ResourceBundleResourceMockFactory.no_contact_resource_fetch()
        self.old_fetch = Resource.fetch
        Resource.fetch = mock_fetch

        super(TestBLLAutochecks, self).setUp()

    def tearDown(self):
        Resource.fetch = self.old_fetch
        super(TestBLLAutochecks, self).tearDown()

    def test_01_annotate_application(self):
        source = ApplicationFixtureFactory.make_application_source()
        application = models.Application(**source)
        application.save(blocking=True)

        ma = AutocheckMockFactory.mock_autochecker()
        anno_svc = DOAJ.autochecksService([(True, True, ma)])
        anno_svc.autocheck_application(application)

        time.sleep(2)

        application = models.Application.pull(application.id)
        autocheck = models.Autocheck.for_application(application.id)

        # assert application.application_status == constants.APPLICATION_STATUS_PENDING
        assert autocheck is not None
        assert autocheck.application == application.id
        assert len(autocheck.checks) == 1

    def test_02_annotate_journal(self):
        source = JournalFixtureFactory.make_journal_source()
        journal = models.Journal(**source)
        journal.save(blocking=True)

        ma = AutocheckMockFactory.mock_autochecker()
        anno_svc = DOAJ.autochecksService([(True, True, ma)])
        anno_svc.autocheck_journal(journal)

        time.sleep(2)

        journal = models.Journal.pull(journal.id)
        autocheck = models.Autocheck.for_journal(journal.id)

        # assert application.application_status == constants.APPLICATION_STATUS_PENDING
        assert autocheck is not None
        assert autocheck.journal == journal.id
        assert len(autocheck.checks) == 1

    def test_03_dismiss_undismiss(self):
        autocheck = models.Autocheck()
        autocheck.application = "test_application"
        check = autocheck.add_check("field", "original", "suggested", "advice", "reference", {"context": "here"}, "test")
        autocheck.save(blocking=True)

        anno_svc = DOAJ.autochecksService()
        anno_svc.dismiss(autocheck.id, check.get("id"))

        time.sleep(2)

        ac2 = models.Autocheck.for_application("test_application")
        assert ac2.checks[0].get("dismissed") is True

        anno_svc.undismiss(autocheck.id, check.get("id"))

        time.sleep(2)

        ac3 = models.Autocheck.for_application("test_application")
        assert ac3.checks[0].get("dismissed", False) is False
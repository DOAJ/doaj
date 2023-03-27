import time

from portality import constants
from doajtest.helpers import DoajTestCase
from portality.core import app
from portality import models
from portality.tasks.application_annotations import ApplicationAnnotations
from portality.background import BackgroundApi
from portality.bll import DOAJ

from doajtest.fixtures import ApplicationFixtureFactory, JournalFixtureFactory
from doajtest.mocks.annotation_resource_bundle_Resource import ResourceBundleResourceMockFactory
from doajtest.mocks.annotation_annotators import AnnotatorsMockFactory

from portality.annotation.resource_bundle import Resource


class TestBLLAnnotations(DoajTestCase):

    def setUp(self):
        mock_fetch = ResourceBundleResourceMockFactory.no_contact_resource_fetch()
        self.old_fetch = Resource.fetch
        Resource.fetch = mock_fetch

        super(TestBLLAnnotations, self).setUp()

    def tearDown(self):
        Resource.fetch = self.old_fetch
        super(TestBLLAnnotations, self).tearDown()

    def test_01_annotate_application(self):
        source = ApplicationFixtureFactory.make_application_source()
        application = models.Application(**source)
        application.save(blocking=True)

        ma = AnnotatorsMockFactory.mock_annotator()
        anno_svc = DOAJ.annotationsService([(True, True, ma)])
        anno_svc.annotate_application(application)

        time.sleep(2)

        application = models.Application.pull(application.id)
        annotation = models.Annotation.for_application(application.id)

        # assert application.application_status == constants.APPLICATION_STATUS_PENDING
        assert annotation is not None
        assert annotation.application == application.id
        assert len(annotation.annotations) == 1

    def test_01_annotate_journal(self):
        source = JournalFixtureFactory.make_journal_source()
        journal = models.Journal(**source)
        journal.save(blocking=True)

        ma = AnnotatorsMockFactory.mock_annotator()
        anno_svc = DOAJ.annotationsService([(True, True, ma)])
        anno_svc.annotate_journal(journal)

        time.sleep(2)

        journal = models.Journal.pull(journal.id)
        annotation = models.Annotation.for_journal(journal.id)

        # assert application.application_status == constants.APPLICATION_STATUS_PENDING
        assert annotation is not None
        assert annotation.journal == journal.id
        assert len(annotation.annotations) == 1



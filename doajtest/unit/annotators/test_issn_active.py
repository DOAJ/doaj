from doajtest.helpers import DoajTestCase
from doajtest.fixtures import ApplicationFixtureFactory
from doajtest.mocks.annotation_resource_bundle_Resource import ResourceBundleResourceMockFactory

from portality.annotation.annotators.issn_active import ISSNActive
from portality import models
from portality.annotation.resource_bundle import Resource, ResourceBundle


class TestISSNActive(DoajTestCase):
    def setUp(self):
        self.old_fetch = Resource.fetch
        super(TestISSNActive, self).setUp()

    def tearDown(self):
        Resource.fetch = self.old_fetch
        super(TestISSNActive, self).tearDown()

    def test_01_issn_fetch_fail(self):
        Resource.fetch = ResourceBundleResourceMockFactory.fail_fetch()

        issn_active = ISSNActive()

        form = {
            "pissn": "1234-5678",
            "eissn": "9876-5432"
        }

        source = ApplicationFixtureFactory.make_application_source()
        app = models.Application(**source)

        annotations = models.Annotation()
        resources = ResourceBundle()

        issn_active.annotate(form, app, annotations, resources, logger=lambda x: x)

        assert len(annotations.annotations) == 2
        for anno in annotations.annotations:
            assert anno.get("advice") == issn_active.UNABLE_TO_ACCESS

    def test_02_not_found(self):
        Resource.fetch = ResourceBundleResourceMockFactory.not_found_fetch()

        issn_active = ISSNActive()

        form = {
            "pissn": "1234-5678",
            "eissn": "9876-5432"
        }

        source = ApplicationFixtureFactory.make_application_source()
        app = models.Application(**source)

        annotations = models.Annotation()
        resources = ResourceBundle()

        issn_active.annotate(form, app, annotations, resources, logger=lambda x: x)

        assert len(annotations.annotations) == 2
        for anno in annotations.annotations:
            assert anno.get("advice") == issn_active.NOT_FOUND

    def test_03_fully_validated(self):
        Resource.fetch = ResourceBundleResourceMockFactory.no_contact_resource_fetch(version="Register")

        issn_active = ISSNActive()

        form = {
            "pissn": "1234-5678",
            "eissn": "9876-5432"
        }

        source = ApplicationFixtureFactory.make_application_source()
        app = models.Application(**source)

        annotations = models.Annotation()
        resources = ResourceBundle()

        issn_active.annotate(form, app, annotations, resources, logger=lambda x: x)

        assert len(annotations.annotations) == 2
        for anno in annotations.annotations:
            assert anno.get("advice") == issn_active.FULLY_VALIDATED

    def test_04_not_validated(self):
        Resource.fetch = ResourceBundleResourceMockFactory.no_contact_resource_fetch(version="Pending")

        issn_active = ISSNActive()

        form = {
            "pissn": "1234-5678",
            "eissn": "9876-5432"
        }

        source = ApplicationFixtureFactory.make_application_source()
        app = models.Application(**source)

        annotations = models.Annotation()
        resources = ResourceBundle()

        issn_active.annotate(form, app, annotations, resources, logger=lambda x: x)

        assert len(annotations.annotations) == 2
        for anno in annotations.annotations:
            assert anno.get("advice") == issn_active.NOT_VALIDATED
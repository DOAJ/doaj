from doajtest.helpers import DoajTestCase
from doajtest.fixtures import ApplicationFixtureFactory
from doajtest.mocks.annotation_resource_bundle_Resource import ResourceBundleResourceMockFactory

from portality.annotation.annotators.issn_active import ISSNActive
from portality import models
from portality.annotation.resource_bundle import Resource, ResourceBundle

import responses    # mocks for the requests library


class TestISSNOrg(DoajTestCase):
    def setUp(self):
        super(TestISSNOrg, self).setUp()

    def tearDown(self):
        super(TestISSNOrg, self).tearDown()

    @responses.activate
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
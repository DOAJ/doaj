from doajtest.helpers import DoajTestCase
from doajtest.fixtures import ApplicationFixtureFactory, IssnOrgFixtureFactory
from doajtest.mocks.autocheck_resource_bundle_Resource import ResourceBundleResourceMockFactory

from portality.autocheck.checkers.issn_active import ISSNActive
from portality import models
from portality.autocheck.resource_bundle import Resource, ResourceBundle, ResourceUnavailable
from portality.autocheck.resources.issn_org import ISSNOrg

import responses    # mocks for the requests library


class TestResource(DoajTestCase):
    def setUp(self):
        super(TestResource, self).setUp()

    def tearDown(self):
        super(TestResource, self).tearDown()

    def test_01_resource_bundle(self):
        resources = ResourceBundle()

        resinst = Resource(resources)
        resinst.fetch_fresh = lambda *args, **kwargs: {"test": "data"}
        data = resinst.fetch("arbitrary_resource")

        assert data == {"test": "data"}
        assert resources.get(resinst.make_resource_id()) == {"test": "data"}

    def test_02_resource_unavailable(self):
        resources = ResourceBundle()

        resinst = Resource(resources)
        with self.assertRaises(ResourceUnavailable):
            data = resinst.fetch("arbitrary_resource")

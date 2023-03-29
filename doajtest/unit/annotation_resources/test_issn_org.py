from doajtest.helpers import DoajTestCase
from doajtest.fixtures import ApplicationFixtureFactory, IssnOrgFixtureFactory
from doajtest.mocks.annotation_resource_bundle_Resource import ResourceBundleResourceMockFactory

from portality.annotation.annotators.issn_active import ISSNActive
from portality import models
from portality.annotation.resource_bundle import Resource, ResourceBundle
from portality.annotation.resources.issn_org import ISSNOrg

import responses    # mocks for the requests library


class TestISSNOrg(DoajTestCase):
    def setUp(self):
        super(TestISSNOrg, self).setUp()

    def tearDown(self):
        super(TestISSNOrg, self).tearDown()

    @responses.activate
    def test_01_issn_fetch(self):
        resources = ResourceBundle()
        issn_org = ISSNOrg(resources)

        rsp1 = responses.Response(
            method="GET",
            url=issn_org.reference_url("1234-5678"),
            body=IssnOrgFixtureFactory.web_page_body()
        )
        responses.add(rsp1)

        data = issn_org.fetch("1234-5678")

        assert data is not None
        assert data.is_registered()

from doajtest.helpers import DoajTestCase
from doajtest.fixtures import ApplicationFixtureFactory
from doajtest.mocks.autocheck_resource_bundle_Resource import ResourceBundleResourceMockFactory

from portality.autocheck.checkers.keepers_registry import KeepersRegistry
from portality import models
from portality.autocheck.resource_bundle import Resource, ResourceBundle


class TestKeepersRegistry(DoajTestCase):
    def setUp(self):
        self.old_fetch = Resource.fetch
        super(TestKeepersRegistry, self).setUp()

    def tearDown(self):
        Resource.fetch = self.old_fetch
        super(TestKeepersRegistry, self).tearDown()

    # Note that we do not test the failure to fetch cases as they are already covered
    # by the ISSNActive tests

    def test_01_registered(self):
        Resource.fetch = ResourceBundleResourceMockFactory.no_contact_resource_fetch(archive_components={
            "CLOCKSS": True,
            "LOCKSS": True,
            "Internet Archive": False
        })

        kr = KeepersRegistry()

        form = {
            "pissn": "1234-5678",
            "eissn": "9876-5432",
            "preservation_service": ["LOCKSS", "Internet Archive", "PKP PN"]
        }

        source = ApplicationFixtureFactory.make_application_source()
        app = models.Application(**source)

        autochecks = models.Autocheck()
        resources = ResourceBundle()

        kr.check(form, app, autochecks, resources, logger=lambda x: x)

        assert len(autochecks.checks) == 3

        checks = [False, False, False]
        for check in autochecks.checks:
            if check["context"]["service"] == "LOCKSS":
                assert check["advice"] == kr.PRESENT
                checks[0] = True

            if check["context"]["service"] == "Internet Archive":
                assert check["advice"] == kr.OUTDATED
                checks[1] = True

            if check["context"]["service"] == "PKP PN":
                assert check["advice"] == kr.MISSING
                checks[2] = True

        assert all(checks)
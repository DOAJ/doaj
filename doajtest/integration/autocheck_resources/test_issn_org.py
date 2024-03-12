from doajtest.helpers import DoajTestCase

from portality.autocheck.resource_bundle import Resource, ResourceBundle
from portality.autocheck.resources.issn_org import ISSNOrg

#########################################
# We're expecting the following ISSNs to resolve to pages which embed schema.org data
# which have the following properties:
#
# * provisional - the ISSN is provisional, so the property mainEntityOfPage.version is not "Register"
# * archived - the ISSN is archived, so the property subjectOf contains at least one ArchiveComponent
# * registered - the ISSN is registered, so the property mainEntityOfPage.version is "Register"

TESTS = {
    "2786-5800": ["provisional"],
    "2673-8198": ["archived"],
    "1234-1231": ["registered"]
}


class TestISSNOrg(DoajTestCase):
    def setUp(self):
        super(TestISSNOrg, self).setUp()

    def tearDown(self):
        super(TestISSNOrg, self).tearDown()

    def test_01_integrations(self):
        resources = ResourceBundle()
        issn_org = ISSNOrg(resources)

        for issn, expected in TESTS.items():
            data = issn_org.fetch(issn)

            if "provisional" in expected:
                assert data is not None
                assert data.is_registered() is False

            if "archived" in expected:
                assert data is not None
                assert len(data.archive_components) > 0

                for ac in data.archive_components:
                    id = ac.get("holdingArchive", {}).get("@id")
                    tc = ac.get("temporalCoverage")
                    assert id is not None
                    assert tc is not None

            if "registered" in expected:
                assert data is not None
                assert data.is_registered() is True



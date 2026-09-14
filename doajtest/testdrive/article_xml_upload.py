from doajtest.testdrive.factory import TestDrive
from portality import models

# Shared by all three yml files in the "Article XML Upload" suite
# (article_doaj_xml_upload.yml, crossref-4.4.2.yml, crossref-5.3.1.yml). Unlike most
# testdrives, the ISSNs here are FIXED, not randomised - the XML files being uploaded
# are static, checked-in fixtures with these exact values hardcoded into their content
# (e.g. successful.xml, update.xml, duplicate_in_file.xml all contain pissn 1111-1111 /
# eissn 2222-2222). The testdrive's job is to make the database match what's already
# fixed in those files, not the other way around - so don't run this testdrive twice
# without tearing down first, or you'll get two journals matching the same ISSN.

PISSN = "1111-1111"
EISSN = "2222-2222"
# "unowned ISSN" third-party journal - the DOAJ-native and Crossref XML fixtures use
# a different print ISSN each, so this testdrive provisions one journal per format.
THIRD_PARTY_PISSN_DOAJ = "0000-0000"
THIRD_PARTY_PISSN_CROSSREF = "0000-0002"
THIRD_PARTY_EISSN = "0000-000X"


class ArticleXmlUpload(TestDrive):
    def setup(self) -> dict:
        publisher_acc, publisher_pw = self.publisher_account()
        journal = self.journal(
            in_doaj=True,
            title=f"Successful {self.run_seed}",
            owner=publisher_acc.id,
            pissn=PISSN,
            eissn=EISSN,
        )

        # Owned by someone else entirely, for the "unowned ISSN" tests - the tester
        # never needs to log into this account, it just needs to exist.
        third_party_acc, third_party_pw = self.publisher_account()
        third_party_doaj = self.journal(
            in_doaj=True,
            title=f"Third Party DOAJ {self.run_seed}",
            owner=third_party_acc.id,
            pissn=THIRD_PARTY_PISSN_DOAJ,
            eissn=THIRD_PARTY_EISSN,
        )
        third_party_crossref = self.journal(
            in_doaj=True,
            title=f"Third Party Crossref {self.run_seed}",
            owner=third_party_acc.id,
            pissn=THIRD_PARTY_PISSN_CROSSREF,
            eissn=THIRD_PARTY_EISSN,
        )

        report = {
            "notes": [
                "Log in as 'publisher' to run the tests in article_doaj_xml_upload.yml, "
                "crossref-4.4.2.yml and crossref-5.3.1.yml - they all upload static XML "
                "files that hardcode print ISSN 1111-1111 / online ISSN 2222-2222 for "
                "the 'Successful' journal this account owns.",
                "For the 'unowned ISSN' tests: DOAJ-native's file uses ISSN 0000-0000, "
                "the Crossref files (both versions) use 0000-0002 - both are provisioned "
                "here, owned by a different account, not 'publisher'. You don't need to "
                "log into that account.",
                "The 'withdrawn journal' test in article_doaj_xml_upload.yml needs its "
                "own separate testdrive (article_xml_upload_withdrawn) - its fixed ISSN "
                "collides with the ones used here, so run the two one at a time, never "
                "both at once.",
                "The 'Successful' journal must stay free of articles between test runs "
                "for the 'successful'/'update' tests to behave correctly - use the "
                "teardown link and re-run this testdrive for a clean slate if you need "
                "to restart partway through the suite.",
            ],
            "accounts": {
                "publisher": {"username": publisher_acc.id, "password": publisher_pw},
            },
            "journals": {
                "Successful (publisher-owned)": {"id": journal.id, "pissn": PISSN, "eissn": EISSN},
                "Third Party DOAJ-native (not publisher-owned)": {
                    "id": third_party_doaj.id, "pissn": THIRD_PARTY_PISSN_DOAJ, "eissn": THIRD_PARTY_EISSN,
                },
                "Third Party Crossref (not publisher-owned)": {
                    "id": third_party_crossref.id, "pissn": THIRD_PARTY_PISSN_CROSSREF, "eissn": THIRD_PARTY_EISSN,
                },
            },
            "non_renderable": {
                "third_party_account": third_party_acc.id,
            },
        }
        return report

    def teardown(self, params) -> dict:
        models.Account.remove_by_id(params["accounts"]["publisher"]["username"])
        models.Account.remove_by_id(params["non_renderable"]["third_party_account"])
        for j in params["journals"].values():
            models.Journal.remove_by_id(j["id"])
        # sweep up any articles the live upload tests created against these fixed
        # ISSNs, regardless of which journal "version" they were matched to at the time.
        # Split into two calls so a collision on the third-party ISSNs (unrelated real
        # articles can share these, e.g. "0000-0000" is a common placeholder for a missing
        # eissn) can't block clearing PISSN/EISSN, which the "successful"/"update" tests
        # depend on being article-free between runs.
        self.safe_delete_by_issns([PISSN, EISSN])
        self.safe_delete_by_issns([THIRD_PARTY_PISSN_DOAJ, THIRD_PARTY_PISSN_CROSSREF, THIRD_PARTY_EISSN])
        return self.SUCCESS

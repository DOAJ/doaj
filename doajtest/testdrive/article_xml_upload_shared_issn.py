from doajtest.testdrive.factory import TestDrive
from portality import models

# For the "Upload a file containing ISSNs erroneously shared with another account"
# test only (shared_issn.xml, present in all 3 yml files in this suite). Kept
# separate from article_xml_upload because this scenario needs eissn 2222-2222 to be
# shared between two DIFFERENT journals (one the publisher's, one someone else's) -
# if that lived in the main fixture, it would break every other test's assumption
# that 2222-2222 unambiguously identifies the publisher's one "Successful" journal.

PISSN = "1111-1111"
EISSN = "2222-2222"


class ArticleXmlUploadSharedIssn(TestDrive):
    def setup(self) -> dict:
        publisher_acc, publisher_pw = self.publisher_account()
        journal = self.journal(
            in_doaj=True,
            title=f"Successful {self.run_seed}",
            owner=publisher_acc.id,
            pissn=PISSN,
            eissn=EISSN,
        )

        # A second, unrelated journal that also claims eissn 2222-2222 - the
        # "erroneous" shared ISSN this test is about. Its own pissn is random so it
        # doesn't also collide with 1111-1111.
        other_acc, other_pw = self.publisher_account()
        other_journal = self.journal(
            in_doaj=True,
            title=f"Also Claims 2222-2222 {self.run_seed}",
            owner=other_acc.id,
            eissn=EISSN,
        )

        return {
            "notes": [
                "Log in as 'publisher' to run the 'Upload a file containing ISSNs "
                "erroneously shared with another account' test in "
                "article_doaj_xml_upload.yml, crossref-4.4.2.yml and crossref-5.3.1.yml.",
                "eissn 2222-2222 is deliberately attached to two different journals here "
                "(this account's, and another account's) - this is a standalone "
                "testdrive, separate from article_xml_upload, because that shared state "
                "would break every other test's assumption that 2222-2222 unambiguously "
                "belongs to one journal.",
            ],
            "accounts": {
                "publisher": {"username": publisher_acc.id, "password": publisher_pw},
            },
            "journals": {
                "Successful (publisher-owned)": {"id": journal.id, "pissn": PISSN, "eissn": EISSN},
                "Other (shares eissn 2222-2222)": {"id": other_journal.id, "eissn": EISSN},
            },
            "non_renderable": {
                "other_account": other_acc.id,
            },
        }

    def teardown(self, params) -> dict:
        models.Account.remove_by_id(params["accounts"]["publisher"]["username"])
        models.Account.remove_by_id(params["non_renderable"]["other_account"])
        for j in params["journals"].values():
            models.Journal.remove_by_id(j["id"])
        self.safe_delete_by_issns([PISSN, EISSN])
        return self.SUCCESS

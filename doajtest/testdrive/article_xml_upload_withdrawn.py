from doajtest.testdrive.factory import TestDrive
from portality import models

# For article_doaj_xml_upload.yml's "Upload a file containing ISSN that has been
# withdrawn" test only. Kept as a separate testdrive from article_xml_upload
# because withdrawn_journal.xml hardcodes pissn 0000-0000 - the same ISSN
# article_xml_upload uses for its "third party" journal, just in an incompatible
# state (in DOAJ vs withdrawn). Run this one on its own, torn down before or after
# article_xml_upload, never at the same time as it.

PISSN = "0000-0000"


class ArticleXmlUploadWithdrawn(TestDrive):
    def setup(self) -> dict:
        publisher_acc, publisher_pw = self.publisher_account()
        journal = self.journal(
            in_doaj=False,
            title=f"Withdrawn {self.run_seed}",
            owner=publisher_acc.id,
            pissn=PISSN,
        )

        return {
            "notes": [
                "Log in as 'publisher' to run the 'Upload a file containing ISSN that "
                "has been withdrawn' test in article_doaj_xml_upload.yml.",
                "This journal's ISSN (0000-0000) is fixed to match withdrawn_journal.xml, "
                "and deliberately collides with the ISSN used by the article_xml_upload "
                "testdrive's 'third party' journal - don't run both testdrives at once.",
            ],
            "accounts": {
                "publisher": {"username": publisher_acc.id, "password": publisher_pw},
            },
            "journals": {
                "Withdrawn": {"id": journal.id, "pissn": PISSN},
            },
        }

    def teardown(self, params) -> dict:
        models.Account.remove_by_id(params["accounts"]["publisher"]["username"])
        for j in params["journals"].values():
            models.Journal.remove_by_id(j["id"])
        self.safe_delete_by_issns([PISSN])
        return self.SUCCESS

from portality import constants
from doajtest.testdrive.factory import TestDrive
from doajtest.fixtures.v2.journals import JournalFixtureFactory
from doajtest.fixtures.article import ArticleFixtureFactory
from portality import models
from portality.core import app

# ISSNs and article DOIs/fulltext URLs below are fixed (not randomised) to match
# doajtest/xml_upload_test_package/admin_metadata_form_test_pack.xml, which is what
# the admin_article_metadata_form testbook test expects to see on the form.
JOURNAL_PISSN = "1234-5678"
JOURNAL_EISSN = "9876-5432"
EXCLUDED_JOURNAL_PISSN = "0000-0000"

ARTICLE_SUFFIXES = ["100", "200", "300"]


class AdminArticleMetadataForm(TestDrive):
    def setup(self) -> dict:
        admin_un = self.create_random_str()
        admin_pw = self.create_random_str()
        admin_acc = models.Account.make_account(
            admin_un + "@example.com", admin_un, "Admin " + admin_un, [constants.ROLE_ADMIN]
        )
        admin_acc.set_password(admin_pw)
        admin_acc.save(blocking=True)

        owner_un = self.create_random_str()
        owner_pw = self.create_random_str()
        owner_acc = models.Account.make_account(
            owner_un + "@example.com", owner_un, "Publisher " + owner_un, [constants.ROLE_PUBLISHER]
        )
        owner_acc.set_password(owner_pw)
        owner_acc.save(blocking=True)

        # Journal in DOAJ that owns the 3 test articles below - the ISSN dropdowns on
        # the admin article metadata form should offer these two ISSNs
        source = JournalFixtureFactory.make_journal_source(in_doaj=True)
        journal = models.Journal(**source)
        journal.remove_current_application()
        journal.set_id(journal.makeid())
        journal.set_owner(owner_acc.id)
        journal.bibjson().title = "Successful"
        journal.bibjson().pissn = JOURNAL_PISSN
        journal.bibjson().eissn = JOURNAL_EISSN
        journal.save(blocking=True)

        # Same owner, but this journal is not in DOAJ - its ISSN must NOT appear in
        # the article form's ISSN dropdowns
        source = JournalFixtureFactory.make_journal_source(in_doaj=False)
        excluded_journal = models.Journal(**source)
        excluded_journal.remove_current_application()
        excluded_journal.set_id(excluded_journal.makeid())
        excluded_journal.set_owner(owner_acc.id)
        excluded_journal.bibjson().title = "Not In DOAJ"
        excluded_journal.bibjson().pissn = EXCLUDED_JOURNAL_PISSN
        excluded_journal.save(blocking=True)

        base = app.config.get("BASE_URL", "")
        articles = {}
        for suffix in ARTICLE_SUFFIXES:
            a_source = ArticleFixtureFactory.make_article_source(
                pissn=JOURNAL_PISSN, eissn=JOURNAL_EISSN, with_id=True, in_doaj=True,
                doi=f"10.1234/{suffix}", fulltext=f"http://doaj.org/testing/{suffix}.pdf"
            )
            a = models.Article(**a_source)
            a.bibjson().title = f"Success {suffix}"
            a.set_id(a.makeid())
            a.save(blocking=True)
            articles[f"Success {suffix}"] = {
                "id": a.id,
                "admin_metadata_form": base + "/admin/article/" + a.id,
            }

        return {
            "notes": [
                "Log in as the 'admin' account to test the admin article metadata form.",
                "The 'owner' account owns both journals below - you do not need to log into it.",
                "'Successful' is in DOAJ and holds the 3 test articles.",
                "'Not In DOAJ' is owned by the same account, but is not in DOAJ - its ISSN "
                "must not appear in the article form's ISSN dropdowns.",
            ],
            "accounts": {
                "admin": {"username": admin_acc.id, "password": admin_pw},
                "owner": {"username": owner_acc.id, "password": owner_pw},
            },
            "journals": {
                "Successful": journal.id,
                "Not In DOAJ": excluded_journal.id,
            },
            "articles": articles,
        }

    def teardown(self, params) -> dict:
        models.Account.remove_by_id(params["accounts"]["admin"]["username"])
        models.Account.remove_by_id(params["accounts"]["owner"]["username"])
        for jid in params["journals"].values():
            models.Journal.remove_by_id(jid)
        for article in params["articles"].values():
            models.Article.remove_by_id(article["id"])
        return self.SUCCESS

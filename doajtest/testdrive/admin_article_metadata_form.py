from portality import constants
from doajtest.testdrive.factory import TestDrive
from doajtest.fixtures.v2.journals import JournalFixtureFactory
from doajtest.fixtures.article import ArticleFixtureFactory
from portality import models
from portality.core import app

# Titles are fixed so the testbook steps can refer to articles by name; every
# identifier that could collide across runs (ISSNs, DOIs, fulltext URLs) is
# generated fresh instead, and reported back so a tester can copy the real values.
ARTICLE_TITLES = ["Success 100", "Success 200", "Success 300"]


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

        pissn = self.generate_unique_issn()
        eissn = self.generate_unique_issn()
        excluded_pissn = self.generate_unique_issn()

        # Journal in DOAJ that owns the test articles below - the ISSN dropdowns on
        # the admin article metadata form should offer these two ISSNs
        source = JournalFixtureFactory.make_journal_source(in_doaj=True)
        journal = models.Journal(**source)
        journal.remove_current_application()
        journal.set_id(journal.makeid())
        journal.set_owner(owner_acc.id)
        journal.bibjson().title = "Successful " + self.run_seed
        journal.bibjson().pissn = pissn
        journal.bibjson().eissn = eissn
        journal.save(blocking=True)

        # Same owner, but this journal is not in DOAJ - its ISSN must NOT appear in
        # the article form's ISSN dropdowns
        source = JournalFixtureFactory.make_journal_source(in_doaj=False)
        excluded_journal = models.Journal(**source)
        excluded_journal.remove_current_application()
        excluded_journal.set_id(excluded_journal.makeid())
        excluded_journal.set_owner(owner_acc.id)
        excluded_journal.bibjson().title = "Not In DOAJ " + self.run_seed
        excluded_journal.bibjson().pissn = excluded_pissn
        excluded_journal.save(blocking=True)

        base = app.config.get("BASE_URL", "")
        articles = {}
        for title in ARTICLE_TITLES:
            doi = f"10.{self.create_random_str(n_char=4)}/{self.create_random_str(n_char=6)}"
            fulltext = f"http://doaj.org/testing/{self.create_random_str(n_char=8)}.pdf"
            a_source = ArticleFixtureFactory.make_article_source(
                pissn=pissn, eissn=eissn, with_id=True, in_doaj=True,
                doi=doi, fulltext=fulltext
            )
            a = models.Article(**a_source)
            a.bibjson().title = title
            a.set_id(a.makeid())
            # Mirrors what create_article(add_journal_info=True) does on real submission
            # of this form, so the journal sub-record looks like a real one, not the
            # ArticleFixtureFactory placeholder ("The Publisher" / "The Title" / etc.)
            a.add_journal_metadata(j=journal)
            a.save(blocking=True)
            articles[title] = {
                "id": a.id,
                "doi": doi,
                "fulltext_url": fulltext,
                "admin_metadata_form": base + "/admin/article/" + a.id,
            }

        return {
            "notes": [
                "Log in as the 'admin' account to test the admin article metadata form.",
                "The 'owner' account owns both journals below - you do not need to log into it.",
                "'Successful ...' is in DOAJ and holds the 3 test articles.",
                "'Not In DOAJ ...' is owned by the same account, but is not in DOAJ - its ISSN "
                "must not appear in the article form's ISSN dropdowns.",
                "ISSNs, DOIs and fulltext URLs are freshly generated every run - always use the "
                "values shown below, not any hardcoded numbers from an old test script.",
            ],
            "accounts": {
                "admin": {"username": admin_acc.id, "password": admin_pw},
                "owner": {"username": owner_acc.id, "password": owner_pw},
            },
            "journals": {
                "Successful": {"id": journal.id, "pissn": pissn, "eissn": eissn},
                "Not In DOAJ": {"id": excluded_journal.id, "pissn": excluded_pissn},
            },
            "articles": articles,
        }

    def teardown(self, params) -> dict:
        models.Account.remove_by_id(params["accounts"]["admin"]["username"])
        models.Account.remove_by_id(params["accounts"]["owner"]["username"])
        for j in params["journals"].values():
            models.Journal.remove_by_id(j["id"])
        for article in params["articles"].values():
            models.Article.remove_by_id(article["id"])
        return self.SUCCESS

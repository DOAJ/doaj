from portality import constants
from doajtest.testdrive.factory import TestDrive
from doajtest.fixtures.article import ArticleFixtureFactory
from portality import models

# Covers most of doajtest/testbook/articles_preservation/upload_preservation_files.yml.
# Two of its tests upload static, checked-in zip archives
# (doajtest/preservation_upload_test_package/*.zip) whose identifiers.csv hardcodes
# specific identifiers - a fulltext URL for valid_article.zip, three DOIs for
# multi_journals.zip. Rather than following the yml's old manual instructions
# (download the zip, edit identifiers.csv to reference freshly made articles,
# re-zip), this testdrive creates articles that already match those hardcoded
# identifiers, so the static zip files can be uploaded completely unmodified.

VALID_ARTICLE_URL = "http://revistascientificas.filo.uba.ar/index.php/petm/article/view/8775"
MULTI_JOURNAL_DOIS = {
    "article1": "10.1515/opphil-2020-0159",
    "article2": "10.3389/fbioe.2019.00371",
    "article3": "10.3389/fbioe.2021.679650",
}


class ArticlePreservation(TestDrive):
    def setup(self) -> dict:
        no_preservation_acc, no_preservation_pw = self.publisher_account()

        with_preservation_acc, with_preservation_pw = self.publisher_account()
        with_preservation_acc.add_role(constants.ROLE_PUBLISHER_PRESERVATION)
        with_preservation_acc.save(blocking=True)

        # "Upload correctly structured file..." - owns the article valid_article.zip
        # points at
        valid_journal = self.journal(
            in_doaj=True, owner=with_preservation_acc.id, title=f"Preservation Owned {self.run_seed}"
        )
        valid_article = self._article(valid_journal, fulltext=VALID_ARTICLE_URL)

        # "...with multiple journals..." - 3 journals, one article each, DOIs
        # matching multi_journals.zip's identifiers.csv exactly
        multi = {}
        for article_dir, doi in MULTI_JOURNAL_DOIS.items():
            j = self.journal(
                in_doaj=True, owner=with_preservation_acc.id,
                title=f"Preservation Multi {article_dir} {self.run_seed}",
            )
            a = self._article(j, doi=doi)
            multi[article_dir] = {"journal_id": j.id, "article_id": a.id}

        return {
            "notes": [
                "Log in as 'no_preservation' for the 'Publisher without preservation "
                "role' test - the Preservation tab should NOT be visible.",
                "Log in as 'with_preservation' for every other test in this suite.",
                "For 'Upload correctly structured file...': upload "
                "/preservation_upload_test_package/valid_article.zip exactly as it is "
                "in the repo (no editing needed) - its identifiers.csv already points "
                "at an article owned by 'with_preservation'.",
                "For 'Upload correctly structured file with multiple journals...': "
                "upload /preservation_upload_test_package/multi_journals.zip exactly "
                "as it is (no need to unzip/edit identifiers.csv/re-zip) - its 3 DOIs "
                "already match 3 articles owned by 'with_preservation', one per journal.",
                "For 'articles that user do not own': use the separate "
                "article_preservation_unowned testdrive instead - this testdrive's "
                "article is owned by 'with_preservation', which would make that test "
                "pass for the wrong reason.",
            ],
            "accounts": {
                "no_preservation": {"username": no_preservation_acc.id, "password": no_preservation_pw},
                "with_preservation": {"username": with_preservation_acc.id, "password": with_preservation_pw},
            },
            "journals": {
                "Owned (valid_article.zip)": {"id": valid_journal.id},
                **{f"Multi journal ({k})": {"id": v["journal_id"]} for k, v in multi.items()},
            },
            "articles": {
                "Owned (valid_article.zip)": valid_article.id,
                **{f"Multi article ({k})": v["article_id"] for k, v in multi.items()},
            },
        }

    def _article(self, journal, doi=None, fulltext=None):
        source = ArticleFixtureFactory.make_article_source(
            pissn=journal.bibjson().pissn, eissn=journal.bibjson().eissn,
            with_id=True, in_doaj=True, doi=doi, fulltext=fulltext,
        )
        a = models.Article(**source)
        a.set_id(a.makeid())
        a.save(blocking=True)
        return a

    def teardown(self, params) -> dict:
        for acc in params["accounts"].values():
            models.Account.remove_by_id(acc["username"])
        for j in params["journals"].values():
            models.Journal.remove_by_id(j["id"])
        for aid in params["articles"].values():
            models.Article.remove_by_id(aid)
        return self.SUCCESS

from portality import constants
from doajtest.testdrive.factory import TestDrive
from doajtest.fixtures.article import ArticleFixtureFactory
from portality import models

# For the "Upload correctly structured file with articles that user do not own"
# test only. Kept separate from article_preservation because it needs the same
# fixed fulltext URL (from valid_article.zip's identifiers.csv) to belong to
# someone else's article - the opposite of what article_preservation sets up for
# its own version of that test. Run one at a time.

VALID_ARTICLE_URL = "http://revistascientificas.filo.uba.ar/index.php/petm/article/view/8775"


class ArticlePreservationUnowned(TestDrive):
    def setup(self) -> dict:
        tester_acc, tester_pw = self.publisher_account()
        tester_acc.add_role(constants.ROLE_PUBLISHER_PRESERVATION)
        tester_acc.save(blocking=True)

        other_acc, other_pw = self.publisher_account()
        other_journal = self.journal(in_doaj=True, owner=other_acc.id, title=f"Not Yours {self.run_seed}")
        source = ArticleFixtureFactory.make_article_source(
            pissn=other_journal.bibjson().pissn, eissn=other_journal.bibjson().eissn,
            with_id=True, in_doaj=True, fulltext=VALID_ARTICLE_URL,
        )
        other_article = models.Article(**source)
        other_article.set_id(other_article.makeid())
        other_article.save(blocking=True)

        return {
            "notes": [
                "Log in as 'tester' - it has the preservation role, but does NOT own "
                "the article that valid_article.zip's identifiers.csv points at.",
                "Upload /preservation_upload_test_package/valid_article.zip exactly as "
                "it is in the repo - it should fail (or partially fail) because that "
                "article belongs to a different account, not 'tester'.",
                "This is a separate testdrive from article_preservation, since that one "
                "owns an article at the same fixed URL - don't run both at once.",
            ],
            "accounts": {
                "tester": {"username": tester_acc.id, "password": tester_pw},
            },
            "non_renderable": {
                "other_account": other_acc.id,
            },
            "journals": {
                "Not Yours": {"id": other_journal.id},
            },
            "articles": {
                "Not Yours": other_article.id,
            },
        }

    def teardown(self, params) -> dict:
        models.Account.remove_by_id(params["accounts"]["tester"]["username"])
        models.Account.remove_by_id(params["non_renderable"]["other_account"])
        for j in params["journals"].values():
            models.Journal.remove_by_id(j["id"])
        for aid in params["articles"].values():
            models.Article.remove_by_id(aid)
        return self.SUCCESS

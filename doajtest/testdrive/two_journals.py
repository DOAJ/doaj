from doajtest.fixtures import ArticleFixtureFactory
from doajtest.fixtures.v2.journals import JournalFixtureFactory

from doajtest.testdrive.factory import TestDrive
from portality import models
from portality.models import Journal

atitle = "Investigating Photosynthetic Anomalies in Invisible Ferns"

class TwoJournals(TestDrive):

    def setup(self) -> dict:
        un = "ProfessorWobblethorpe"
        pw = self.create_random_str()
        acc = models.Account.make_account(un + "@mystical.uni.com", un, un, ["admin", "api"])
        acc.set_password(pw)
        api_key = acc.generate_api_key()
        acc.save()

        pissn = self.generate_unique_issn()
        eissn = self.generate_unique_issn()

        source = JournalFixtureFactory.make_journal_source(in_doaj=False)
        jindoaj = Journal(**source)
        jindoaj.set_id(self.create_random_str())
        jindoaj.bibjson().pissn = pissn
        jindoaj.bibjson().eissn = eissn
        jindoaj.bibjson().title = "Transactions of Paradoxical Botany"
        jindoaj.bibjson().journal_url = "https://plants-that-should-not-exist.org"
        jindoaj.save()

        source = JournalFixtureFactory.make_journal_source(in_doaj=True)
        jwithdrawn = Journal(**source)
        jwithdrawn.set_id(self.create_random_str())
        jwithdrawn.bibjson().pissn = pissn
        jwithdrawn.bibjson().eissn = eissn
        jwithdrawn.bibjson().title = "Advanced Transactions of Paradoxical Botany"
        jwithdrawn.bibjson().journal_url = "https://even-stranger-plants.org"
        jwithdrawn.save()

        article = ArticleFixtureFactory.make_incoming_api_article()
        article["bibjson"]["fulltext"] = "https://even-stranger-plants.org/invisible-ferns"
        article["bibjson"]["title"] = atitle
        article["bibjson"]["pissn"] = pissn
        article["bibjson"]["eissn"] = eissn
        article["bibjson"]["journal"] = {
            "volume": "1",
            "number": "99",
            "publisher": "Curious Botanical Press Ltd.",
            "title": "Advanced Transactions of Paradoxical Botany",
            "language": ["EN", "FR"],
            "country": "US"
        }

        return {
            "account": {
                "username": un,
                "password": pw,
                "api key": api_key
            },
            "journals": {
                jindoaj.bibjson().title: jindoaj.id,
                jwithdrawn.bibjson().title: jwithdrawn.id
            },
            "article": {
                atitle: article["id"]
            }
        }

    def teardown(self, params) -> dict:
        models.Account.remove_by_id(params["account"]["username"])
        for k, v in params["journals"].items():
            models.Journal.remove_by_id(v)
        models.Article.remove_by_id(params["article"][atitle])
        return {"status": "success"}

import json

from doajtest.fixtures import ArticleFixtureFactory
from doajtest.fixtures.v2.journals import JournalFixtureFactory

from doajtest.testdrive.factory import TestDrive
from portality import models
from portality.core import app
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

        ids = {
            "pissn": pissn,
            "eissn": eissn
        }

        source = JournalFixtureFactory.make_journal_source(in_doaj=False)
        jindoaj = Journal(**source)
        jindoaj.set_id(self.create_random_str())
        jindoaj.bibjson().pissn = ids["pissn"]
        jindoaj.bibjson().eissn = ids["eissn"]
        jindoaj.bibjson().title = "Transactions of Paradoxical Botany"
        jindoaj.bibjson().journal_url = "https://plants-that-should-not-exist.org"
        del jindoaj.bibjson().replaces
        jindoaj.bibjson().is_replaced_by = [pissn, eissn]
        jindoaj.bibjson().discontinued_date = "2003-03-12"
        jindoaj.save()

        source = JournalFixtureFactory.make_journal_source(in_doaj=True)
        jwithdrawn = Journal(**source)
        jwithdrawn.set_id(self.create_random_str())
        jwithdrawn.bibjson().pissn = ids["pissn"]
        jwithdrawn.bibjson().eissn = ids["eissn"]
        jwithdrawn.bibjson().title = "Advanced Transactions of Paradoxical Botany"
        jwithdrawn.bibjson().journal_url = "https://even-stranger-plants.org"
        jwithdrawn.bibjson().replaces = [pissn, eissn]
        del jwithdrawn.bibjson().is_replaced_by
        del jwithdrawn.bibjson().discontinued_date
        jwithdrawn.save()

        article = ArticleFixtureFactory.make_incoming_api_article(doi="10.000/even-stranger-plants", fulltext="https://even-stranger-plants.org/invisible-ferns")
        article["id"] = self.create_random_str()
        abib = article["bibjson"]
        abib["title"] = atitle
        for ident in abib["identifier"]:
            if ident["type"] in ids:
                ident["id"] = ids[ident["type"]]
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
                jindoaj.bibjson().title: {
                    "id": jindoaj.id,
                    "admin form": app.config.get("BASE_URL", "") + "/admin/journal/" + jindoaj.id
                },
                jwithdrawn.bibjson().title: {
                    "id": jwithdrawn.id,
                    "page": app.config.get("BASE_URL", "") + "/toc/" + pissn
                }
            },
            "article": {
                atitle: article["id"],
                "json": json.dumps(article)
            }
        }

    def teardown(self, params) -> dict:
        models.Account.remove_by_id(params["account"]["username"])
        for k, v in params["journals"].items():
            models.Journal.remove_by_id(v["id"])
        models.Article.remove_by_id(params["article"][atitle])
        return {"status": "success"}

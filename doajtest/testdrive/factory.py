from portality.lib import plugin
import random
import string
from portality import models, constants
from doajtest.fixtures.v2.journals import JournalFixtureFactory
from doajtest.fixtures.article import ArticleFixtureFactory


class TestDrive():

    SUCCESS = {"status": "success"}

    def __init__(self):
        self.run_seed = self.create_random_str()

    def create_random_str(self, n_char=10):
        s = string.ascii_letters + string.digits
        return ''.join(random.choices(s, k=n_char))

    def generate_unique_issn(self):
        while True:
            s = self.create_random_str(n_char=8)
            issn = s[:4] + '-' + s[4:]
            if len(models.Journal.find_by_issn(issn)) == 0 :
                return issn

    def setup(self) -> dict:
        return {"status": "not implemented"}

    def teardown(self, setup_params) -> dict:
        return {"status": "not implemented"}

    ### Reporting functions for consistent delivery of similar data models

    def report_accounts(self, accounts, report):
        report["accounts"] = []
        for acc, pw in accounts:
            report["accounts"].append({
                "username": acc.id,
                "password": pw,
                "api_key": acc.api_key
            })

    def report_journal_ids(self, journals, report):
        report["journals"] = []
        for j in journals:
            report["journals"].append(j.id)

    def report_article_ids(self, articles, report):
        report["articles"] = []
        for a in articles:
            report["articles"].append(a.id)

    def report_article_tombstone_ids(self, tombstones, report):
        report["article_tombstones"] = []
        for a in tombstones:
            report["article_tombstones"].append(a.id)

    def report_script(self, script, name, report):
        report["script"] = {
            "script_name": script,
            "title": name
        }

    ### Teardown methods for consistent cleanup of similar data models

    def teardown_accounts(self, report):
        for acc in report.get("accounts", []):
            models.Account.remove_by_id(acc["username"])

    def teardown_journals(self, report):
        for jid in report.get("journals", []):
            models.Journal.remove_by_id(jid)

    def teardown_articles(self, report):
        for aid in report.get("articles", []):
            models.Article.remove_by_id(aid)

    def teardown_article_tombstones(self, report):
        for tid in report.get("article_tombstones", []):
            models.ArticleTombstone.remove_by_id(tid)

    ### Useful factory methods

    def publisher_account(self, save=True, block=False):
        un = self.create_random_str()
        pw = self.create_random_str()
        acc = models.Account.make_account(un + "@example.com", un, "Publisher " + un, [constants.ROLE_PUBLISHER, constants.ROLE_API])
        acc.set_password(pw)
        acc.generate_api_key()
        if save:
            acc.save(blocking=block)
        return acc, pw

    def journals_in_doaj(self, owner, n=1, save=True, block=False):
        journals = []
        for i in range(n):
            template = {
                "bibjson": {
                    "title": f"Journal {owner} {i} {self.run_seed}",
                }
            }
            source = JournalFixtureFactory.make_journal_source(in_doaj=True, overlay=template)
            j = models.Journal(**source)
            j.remove_current_application()
            j.set_id(j.makeid())
            j.set_owner(owner.id)
            j.bibjson().eissn = self.generate_unique_issn()
            j.bibjson().pissn = self.generate_unique_issn()
            if save:
                j.save(blocking=block)
            journals.append(j)

        return journals

    def articles(self, journal, n=1, save=True):
        articles = []
        for i in range(n):
            eissn = journal.bibjson().eissn
            pissn = journal.bibjson().pissn
            a = ArticleFixtureFactory.make_article_source(eissn=eissn, pissn=pissn, with_id=True, in_doaj=journal.is_in_doaj())
            a = models.Article(**a)
            a.bibjson().title = f"Article {journal.owner} {i} {self.run_seed}"
            a.set_id(a.makeid())
            if save:
                a.save()
            articles.append(a)
        return articles

    def article_tombstones(self, journal, n=1, save=True):
        articles = self.articles(journal, n=n, save=False)

        tombs = []
        for a in articles:
            t = a.make_tombstone()
            if save:
                t.save()
            tombs.append(t)

        return tombs


class TestFactory():
    @classmethod
    def get(cls, test_id):
        modname = test_id
        classname = test_id.replace("_", " ").title().replace(" ", "")
        classpath = "doajtest.testdrive." + modname + "." + classname
        klazz = plugin.load_class(classpath)
        return klazz()
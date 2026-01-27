from doajtest.fixtures import JournalFixtureFactory, ArticleFixtureFactory
from doajtest.testdrive.factory import TestDrive
from portality import models
from portality.models import ArticleTombstone
from portality.dao import DomainObject


class ErrorPages(TestDrive):

    def __init__(self):
        self.aw = None
        self.jw = None
        self.nonexistent_id = None
        self.jp = None

    def generate_journal_source(self, title="New Journal", in_doaj=True):
        j_id = self.create_random_str()
        j_source = JournalFixtureFactory.make_journal_source(in_doaj=in_doaj)
        j_source["id"] = j_id
        j_pissn = self.generate_unique_issn()
        j_eissn = self.generate_unique_issn()
        j_source["bibjson"]["pissn"] = j_pissn
        j_source["bibjson"]["eissn"] = j_eissn
        j_source["bibjson"]["title"] = title

        return j_source

    def setup(self) -> dict:
        ids = []

        jp_title = "Journal in DOAJ"
        jp_source = self.generate_journal_source(jp_title, True)
        jp = models.Journal(**jp_source)
        jp.save(blocking=True)
        ids.append(jp.id)
        jp_bib = jp.bibjson()

        # -----------------------------------------------------------------------------------------------------------

        jw_title = "Withdrawn Journal"
        jw_source = self.generate_journal_source(jw_title, False)
        jw = models.Journal(**jw_source)
        jw.save(blocking=True)
        ids.append(jw.id)
        jw_bib = jw.bibjson()

        # -----------------------------------------------------------------------------------------------------------

        nonexistent_id = self.create_random_str()
        nonexistent_pissn = "xxxx-xxxx"

        # -----------------------------------------------------------------------------------------------------------

        awj_title = "Article from withdrawn journal"
        awj_source = ArticleFixtureFactory.make_article_source(eissn=jw_bib.eissn, pissn=jw_bib.pissn, with_id=False,
                                                              in_doaj=True, with_journal_info=True,
                                                              doi="10.0000/ARTICLE.FROM.WITHDRAWN.JOURNAL")
        awj_id = self.create_random_str()
        awj_source["id"] = awj_id
        awj_source["bibjson"]["title"] = awj_title
        awj = models.Article(**awj_source)
        awj.save(blocking=True)
        ids.append(awj_id)

        # -----------------------------------------------------------------------------------------------------------

        at_title = "Article Tombstone"
        at_source = ArticleFixtureFactory.make_article_source(eissn=self.generate_unique_issn(), pissn=self.generate_unique_issn(), with_id=False,
                                                              in_doaj=True, with_journal_info=True,
                                                              doi="10.0000/ARTICLE.TOMBSTONE")
        at_id = self.create_random_str()
        at_source["id"] = at_id
        at_source["bibjson"]["title"] = at_title
        at = ArticleTombstone(**at_source)
        at.save(blocking=True)
        ids.append(at_id)

        return {
            "non_renderable": ids,
            "urls": {
                "Withdrawn Journal - expect 410:": f'<a href="/toc/{jw_bib.pissn}" target="_blank">{jw_bib.title}</a></br>',
                "Article from withdrawn journal - expect 410": f'<a href="/article/{awj_id}" target="_blank">{awj_title}</a></br>',
                "Deleted Article - expect 410: ": f'<a href="/article/{at_id}" target="_blank">{at_title}</a></br>',
                "Non-existant journal - expect 404:": f'<a href="/toc/{nonexistent_pissn}" target="_blank">Nonexistent Journal</a></br>',
                "Non-existant article - expect 404:": f'<a href="/article/{nonexistent_id}" target="_blank">Nonexistent Article</a>'
            }
        }

    def teardown(self, params):
        for id in params["non_renderable"]:
            DomainObject.remove_by_id(id)

        return {"status": "success"}

# -*- coding: UTF-8 -*-
from parameterized import parameterized
from combinatrix.testintegration import load_parameter_sets

from doajtest.fixtures import ArticleFixtureFactory, JournalFixtureFactory
from doajtest.helpers import DoajTestCase
from portality.bll import DOAJ
from portality.bll import exceptions
from portality import models
from portality.lib.paths import rel2abs
from portality.core import app
from doajtest.mocks.store import StoreMockFactory
from doajtest.mocks.models_Cache import ModelCacheMockFactory
from portality import store, clcsv
from StringIO import StringIO
import os, shutil

def load_cases():
    return load_parameter_sets(rel2abs(__file__, "..", "matrices", "bll_journal_csv"), "journal_csv", "test_id",
                               {"test_id" : []})

EXCEPTIONS = {
    "ArgumentException" : exceptions.ArgumentException,
    "IOError" : IOError
}

class TestBLLJournalCSV(DoajTestCase):

    def setUp(self):
        super(TestBLLJournalCSV, self).setUp()
        self.svc = DOAJ.journalService()

        self.store_tmp_dir = app.config["STORE_TMP_DIR"]
        app.config["STORE_TMP_DIR"] = os.path.join("test_store", "tmp")
        self.store_local_dir = app.config["STORE_LOCAL_DIR"]
        app.config["STORE_LOCAL_DIR"] = os.path.join("test_store", "main")

        self.localStore = store.StoreLocal(None)
        self.tmpStore = store.TempStore()
        self.container_id = app.config.get("STORE_CACHE_CONTAINER")
        self.store_tmp_impl = app.config["STORE_TMP_IMPL"]
        self.store_impl = app.config["STORE_IMPL"]

        self.cache = models.cache.Cache
        models.cache.Cache = ModelCacheMockFactory.in_memory()
        models.Cache = models.cache.Cache

    def tearDown(self):
        app.config["STORE_TMP_IMPL"] = self.store_tmp_impl
        app.config["STORE_IMPL"] = self.store_impl
        if os.path.exists("test_store"):
            shutil.rmtree("test_store")
        self.localStore.delete(self.container_id)
        self.tmpStore.delete(self.container_id)

        models.cache.Cache = self.cache
        models.Cache = self.cache

        super(TestBLLJournalCSV, self).tearDown()

    @parameterized.expand(load_cases)
    def test_journal_csv(self, name, kwargs):

        prune_arg = kwargs.get("prune")
        tmp_write_arg = kwargs.get("tmp_write")
        main_write_arg = kwargs.get("main_write")
        journals_arg = kwargs.get("journals")
        journals_no_issn_arg = kwargs.get("journals_no_issn")
        not_in_doaj_arg = kwargs.get("not_in_doaj")
        journals_with_articles_arg = kwargs.get("journals_with_articles")

        raises_arg = kwargs.get("raises")

        ###############################################
        ## set up

        raises = EXCEPTIONS.get(raises_arg)
        prune = True if prune_arg == "True" else False if prune_arg == "False" else None
        journal_count = int(journals_arg)
        journals_no_issn_count = int(journals_no_issn_arg)
        not_in_doaj_count = int(not_in_doaj_arg)
        journals_with_articles_count = int(journals_with_articles_arg)

        if tmp_write_arg == "fail":
            app.config["STORE_TMP_IMPL"] = StoreMockFactory.no_writes_classpath()

        if main_write_arg == "fail":
            app.config["STORE_IMPL"] = StoreMockFactory.no_writes_classpath()

        journals = []
        if journal_count > 0:
            journals += [models.Journal(**s) for s in JournalFixtureFactory.make_many_journal_sources(count=journal_count, in_doaj=True)]

        comparisons = {}
        articles = []
        for i in range(len(journals)):
            journal = journals[i]
            bj = journal.bibjson()
            bj.alternative_title = u"Заглавие на журнала"   # checking mixed unicode
            issns = journal.bibjson().issns()
            source1 = ArticleFixtureFactory.make_article_source(eissn=issns[0], pissn=issns[1], with_id=False, in_doaj=False)
            articles.append(models.Article(**source1))
            comparisons[issns[0]] = {"issns" : issns, "article_count": 0, "article_latest" : ""}
            if i < journals_with_articles_count:
                source2 = ArticleFixtureFactory.make_article_source(eissn=issns[0], pissn=issns[1], with_id=False, in_doaj=True)
                article2 = models.Article(**source2)
                article2.set_created("2019-0{i}-01T00:00:00Z".format(i=i + 1))
                articles.append(article2)

                source3 = ArticleFixtureFactory.make_article_source(eissn=issns[0], pissn=issns[1], with_id=False, in_doaj=True)
                article3 = models.Article(**source3)
                article3.set_created("2019-0{i}-02T00:00:00Z".format(i=i + 1))
                articles.append(article3)

                comparisons[issns[0]]["article_count"] = 2
                comparisons[issns[0]]["article_latest"] = "2019-0{i}-02T00:00:00Z".format(i=i + 1)

        if journals_no_issn_count > 0:
            noissns = [models.Journal(**s) for s in JournalFixtureFactory.make_many_journal_sources(count=journals_no_issn_count, in_doaj=True)]
            for i in range(len(noissns)):
                noissn = noissns[i]
                bj = noissn.bibjson()
                bj.remove_identifiers(idtype=bj.P_ISSN)
                bj.remove_identifiers(idtype=bj.E_ISSN)
                noissn.set_id("no_issn_{i}".format(i=i))
            journals += noissns

        if not_in_doaj_count > 0:
            nots = [models.Journal(**s) for s in JournalFixtureFactory.make_many_journal_sources(count=not_in_doaj_count, in_doaj=False)]
            for i in range(len(nots)):
                n = nots[i]
                n.set_id("not_in_doaj_{i}".format(i=i))
            journals += nots

        jids = []
        for i in range(len(journals)):
            journals[i].save()
            jids.append((journals[i].id, journals[i].last_updated))

        aids = []
        for i in range(len(articles)):
            articles[i].save()
            aids.append((articles[i].id, articles[i].last_updated))

        if prune:
            self.localStore.store(self.container_id, "journalcsv__doaj_20180101_0000_utf8.csv", source_stream=StringIO("test1"))
            self.localStore.store(self.container_id, "journalcsv__doaj_20180601_0000_utf8.csv", source_stream=StringIO("test2"))
            self.localStore.store(self.container_id, "journalcsv__doaj_20190101_0000_utf8.csv", source_stream=StringIO("test3"))

        models.Journal.blockall(jids)
        models.Article.blockall(aids)

        ###########################################################
        # Execution

        if raises is not None:
            with self.assertRaises(raises):
                self.svc.csv(prune)

                tempFiles = self.tmpStore.list(self.container_id)
                assert len(tempFiles) == 0
        else:
            url, action_register = self.svc.csv(prune)
            assert url is not None

            csv_info = models.cache.Cache.get_latest_csv()
            assert csv_info.get("url") == url

            filenames = self.localStore.list(self.container_id)
            if prune:
                assert len(filenames) == 2
                assert "journalcsv__doaj_20180101_0000_utf8.csv" not in filenames
                assert "journalcsv__doaj_20180601_0000_utf8.csv" not in filenames
                assert "journalcsv__doaj_20190101_0000_utf8.csv" in filenames
            else:
                assert len(filenames) == 1

            latest = None
            for fn in filenames:
                if fn != "journalcsv__doaj_20190101_0000_utf8.csv":
                    latest = fn
                    break

            handle = self.localStore.get(self.container_id, latest, encoding="utf-8")
            reader = clcsv.UnicodeReader(handle)
            rows = [r for r in reader]

            if len(comparisons) > 0:
                expected_headers = JournalFixtureFactory.csv_headers()
                for i in range(len(expected_headers)):
                    h = expected_headers[i]
                    if h != rows[0][i]:
                        print("{x} - {y}".format(x=h, y=rows[0][i]))
                assert rows[0] == expected_headers

                assert len(rows) == journal_count + 1

                for i in range(1, len(rows)):
                    row = rows[i]
                    alt_title = row[2]
                    issn = row[3]
                    eissn = row[4]
                    article_count = int(row[57])
                    article_latest = row[58]

                    assert alt_title == u"Заглавие на журнала"
                    assert issn in comparisons[issn]["issns"]
                    assert eissn in comparisons[issn]["issns"]
                    assert article_count == comparisons[issn]["article_count"], (article_count, comparisons[issn]["article_count"])
                    assert article_latest == comparisons[issn]["article_latest"]

            else:
                assert len(rows) == 0

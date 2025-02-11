import os.path
from io import StringIO

from combinatrix.testintegration import load_parameter_sets
from lxml import etree
from parameterized import parameterized

from doajtest import helpers
from doajtest.fixtures import JournalFixtureFactory, ArticleFixtureFactory
from doajtest.helpers import DoajTestCase
from doajtest.mocks.models_Cache import ModelCacheMockFactory
from doajtest.mocks.store import StoreMockFactory
from portality import models
from portality import store
from portality.bll import DOAJ
from portality.bll import exceptions
from portality.core import app
from portality.lib import nav
from portality.lib.paths import rel2abs
from portality.util import get_full_url_safe, patch_config


def load_cases():
    return load_parameter_sets(rel2abs(__file__, "..", "matrices", "bll_sitemap"), "sitemap", "test_id",
                               {"test_id": []})


EXCEPTIONS = {
    "ArgumentException": exceptions.ArgumentException,
    "IOError": IOError
}


class TestBLLSitemap(DoajTestCase):

    def setUp(self):
        super(TestBLLSitemap, self).setUp()
        self.svc = DOAJ.siteService()

        self.store_local_patcher = helpers.StoreLocalPatcher()
        self.store_local_patcher.setUp(self.app_test)
        self.localStore = store.StoreLocal(None)
        self.tmpStore = store.TempStore()
        self.container_id = app.config.get("STORE_CACHE_CONTAINER")

        self.cache = models.cache.Cache
        models.cache.Cache = ModelCacheMockFactory.in_memory()
        models.Cache = models.cache.Cache

        self.toc_changefreq = app.config["TOC_CHANGEFREQ"]
        app.config["TOC_CHANGEFREQ"] = "daily"

        self.backup_static_entries = app.jinja_env.globals["data"]['nav']['entries']
        app.jinja_env.globals["data"]['nav']['entries'] = self.static_entries = [
            {
                'route': 'doaj.support',
                'entries': [
                    {'route': 'doaj.support'},
                    {'route': 'doaj.sponsors'},
                    {'route': 'ROUTE.THAT.NOT.EXIST'},
                ]
            },
            {
                'entries': [
                    {'route': 'doaj.journals_search'},
                    {'route': 'doaj.articles_search'},
                ]
            }
        ]

        self.base_url = app.config.get("BASE_URL")
        if not self.base_url.endswith("/"):
            self.base_url += "/"

    def tearDown(self):
        self.localStore.delete_container(self.container_id)
        self.tmpStore.delete_container(self.container_id)
        self.store_local_patcher.tearDown(self.app_test)

        models.cache.Cache = self.cache
        models.Cache = self.cache

        app.config["TOC_CHANGEFREQ"] = self.toc_changefreq
        app.jinja_env.globals["data"]['nav']['entries'] = self.backup_static_entries

        super(TestBLLSitemap, self).tearDown()

    @parameterized.expand(load_cases)
    def test_sitemap(self, name, kwargs):

        prune_arg = kwargs.get("prune")
        tmp_write_arg = kwargs.get("tmp_write")
        main_write_arg = kwargs.get("main_write")
        raises_arg = kwargs.get("raises")

        ###############################################
        ## set up

        raises = EXCEPTIONS.get(raises_arg)
        prune = True if prune_arg == "True" else False if prune_arg == "False" else None

        original_configs = {}
        if tmp_write_arg == "fail":
            original_configs.update(patch_config(app, {"STORE_TMP_IMPL": StoreMockFactory.no_writes_classpath()}))

        if main_write_arg == "fail":
            original_configs.update(patch_config(app, {"STORE_IMPL": StoreMockFactory.no_writes_classpath()}))

        journals = []
        for s in JournalFixtureFactory.make_many_journal_sources(count=10, in_doaj=True):
            j = models.Journal(**s)
            j.save()
            journals.append(j)
        models.Journal.blockall([(j.id, j.last_updated) for j in journals])

        expectations = [(j.bibjson().get_preferred_issn(), j.last_updated) for j in journals]

        articles = []
        for s in ArticleFixtureFactory.make_many_article_sources(count=10, in_doaj=True):
            a = models.Article(**s)
            a.save()
            articles.append(a)
        models.Article.blockall([(a.id, a.last_updated) for a in articles])

        articles_expectations = [(a.id, a.last_updated) for a in articles]

        if prune:
            self.localStore.store(self.container_id, "sitemap_doaj_20180101_0000/_0_utf8.xml",
                                  source_stream=StringIO("test1"))
            self.localStore.store(self.container_id, "sitemap_doaj_20180601_0000/_0_utf8.xml",
                                  source_stream=StringIO("test2"))
            self.localStore.store(self.container_id, "sitemap_doaj_20190101_0000/_0_utf8.xml",
                                  source_stream=StringIO("test3"))

        ###########################################################
        # Execution

        if raises is not None:
            with self.assertRaises(raises):
                self.svc.sitemap(prune)

                tempFiles = self.tmpStore.list(self.container_id)
                assert len(tempFiles) == 0, "expected 0, received {}".format(len(tempFiles))
        else:
            url, action_register = self.svc.sitemap(prune)
            assert url is not None

            # Check the results
            ################################
            sitemap_info = models.cache.Cache.get_latest_sitemap()
            assert sitemap_info.get("filename") == url

            filenames = self.localStore.list(self.container_id)
            if prune:
                assert len(filenames) == 2, "expected 0, received {}".format(len(filenames))
                assert "sitemap_doaj_20180101_0000" not in filenames
                assert "sitemap_doaj_20180601_0000" not in filenames
                assert "sitemap_doaj_20190101_0000" in filenames
            else:
                assert len(filenames) == 1, "expected 0, received {}".format(len(filenames))

            latest = None
            for fn in filenames:
                if fn != "sitemap_doaj_20190101_0000":
                    latest = fn
                    break

            NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"

            file_date = '_'.join(latest.split('_')[2:])
            index_file = os.path.join(latest, 'sitemap_index_utf8.xml')

            handle = self.localStore.get(self.container_id, index_file, encoding="utf-8")

            # check sitemap index file
            tree = etree.parse(handle)
            urlElements = tree.getroot().getchildren()
            for urlElement in urlElements:
                loc = urlElement.find(NS + "loc").text
                assert loc.startswith(self.base_url + "sitemap")

            tocs = []
            statics = []
            article_ids = []

            # check sitemap file
            sitemap_file = os.path.join(latest, '_0_utf8.xml')
            handle = self.localStore.get(self.container_id, sitemap_file, encoding="utf-8")

            tree = etree.parse(handle)
            urlElements = tree.getroot().getchildren()

            for urlElement in urlElements:
                loc = urlElement.find(NS + "loc").text
                lm = urlElement.find(NS + "lastmod")
                if lm is not None:
                    lm = lm.text
                cf = urlElement.find(NS + "changefreq").text
                assert cf == "daily"
                # check journals
                if "/toc" in loc:
                    for exp in expectations:
                        if loc.endswith(exp[0]):
                            tocs.append(exp[0])
                            assert lm == exp[1]
                # check articles
                elif "/article/" in loc:
                    for exp in articles_expectations:
                        if loc.endswith(exp[0]):
                            article_ids.append(exp[0])
                            assert lm == exp[1]
                # check static pages
                else:
                    statics.append(loc)
                    assert lm is None
                    assert loc.startswith(app.config.get('BASE_URL', 'https://doaj.org'))

            # deduplicate the list of tocs, to check that we saw all journals
            list(set(tocs))
            assert len(tocs) == len(expectations)

            # deduplicate the list of articles, to check that we saw all articles
            list(set(article_ids))
            assert len(article_ids) == len(articles_expectations)

            # deduplicate the statics, to check we saw all of them too
            _urls = (get_full_url_safe(r)
                     for r in nav.yield_all_route(self.static_entries))
            _urls = filter(None, _urls)
            assert set(statics) == set(_urls)

        # Tear down
        patch_config(app, original_configs)

from parameterized import parameterized
from combinatrix.testintegration import load_parameter_sets

from doajtest.helpers import DoajTestCase
from doajtest.fixtures import JournalFixtureFactory, ArticleFixtureFactory
from doajtest.mocks.store import StoreMockFactory
from doajtest.mocks.model_Cache import ModelCacheMockFactory

from portality.lib.paths import rel2abs
from portality.lib import dates
from portality.background import BackgroundApi
from portality.tasks.public_data_dump import PublicDataDumpBackgroundTask
from portality import models, store
from portality.core import app

import os, shutil
from StringIO import StringIO

def load_cases():
    return load_parameter_sets(rel2abs(__file__, "..", "matrices", "tasks.public_data_dump"), "data_dump", "test_id",
                               {"test_id" : ["1"]})


class TestPublicDataDumpTask(DoajTestCase):

    def setUp(self):
        super(TestPublicDataDumpTask, self).setUp()

        self.store_tmp_imp = app.config.get("STORE_TMP_IMPL")
        self.store_imp = app.config.get("STORE_IMPL")
        self.discovery_records_per_file = app.config.get("DISCOVERY_RECORDS_PER_FILE")
        self.store_local_dir = app.config["STORE_LOCAL_DIR"]
        self.store_tmp_dir = app.config["STORE_TMP_DIR"]
        self.cache = models.Cache

        app.config["STORE_IMPL"] = "portality.store.StoreLocal"
        app.config["STORE_LOCAL_DIR"] = rel2abs(__file__, "..", "tmp", "store", "main")
        app.config["STORE_TMP_DIR"] = rel2abs(__file__, "..", "tmp", "store", "tmp")
        os.makedirs(app.config["STORE_LOCAL_DIR"])
        os.makedirs(app.config["STORE_TMP_DIR"])

        models.Cache = ModelCacheMockFactory.in_memory()

    def tearDown(self):
        app.config["STORE_TMP_IMPL"] = self.store_tmp_imp
        app.config["STORE_IMPL"] = self.store_imp
        app.config["DISCOVERY_RECORDS_PER_FILE"] = self.discovery_records_per_file

        shutil.rmtree(rel2abs(__file__, "..", "tmp"))
        app.config["STORE_LOCAL_DIR"] = self.store_local_dir
        app.config["STORE_TMP_DIR"] = self.store_tmp_dir

        models.Cache = self.cache

        super(TestPublicDataDumpTask, self).tearDown()

    @parameterized.expand(load_cases)
    def test_public_data_dump(self, name, kwargs):

        clean_arg = kwargs.get("clean")
        prune_arg = kwargs.get("prune")
        types_arg = kwargs.get("types")
        journals_arg = kwargs.get("journals")
        articles_arg = kwargs.get("articles")
        batch_size_arg = kwargs.get("batch_size")
        tmp_write_arg = kwargs.get("tmp_write")
        store_write_arg = kwargs.get("store_write")

        status_arg = kwargs.get("status")

        ###############################################
        ## set up

        clean = True if clean_arg == "yes" else False if clean_arg == "no" else None
        prune = True if prune_arg == "yes" else False if prune_arg == "no" else None
        types = types_arg if types_arg != "-" else None

        container_id = app.config["STORE_PUBLIC_DATA_DUMP_CONTAINER"]
        localStore = store.StoreLocal(None)
        if clean or prune:
            for i in range(5):
                localStore.store(container_id, "doaj_article_data_2018-01-0" + str(i) + ".tar.gz",
                                 source_stream=StringIO("test"))
                localStore.store(container_id, "doaj_journal_data_2018-01-0" + str(i) + ".tar.gz",
                                 source_stream=StringIO("test"))

        journal_count = int(journals_arg)
        article_count = int(articles_arg)
        batch_size = int(batch_size_arg)

        sources = JournalFixtureFactory.make_many_journal_sources(journal_count, in_doaj=True)
        for i in range(len(sources)):
            source = sources[i]
            journal = models.Journal(**source)
            journal.save(blocking=i == len(sources) - 1)

        for i in range(article_count):
            source = ArticleFixtureFactory.make_article_source(
                eissn="{x}000-0000".format(x=i),
                pissn="0000-{x}000".format(x=i),
                with_id=False,
                doi="10.123/{x}".format(x=i),
                fulltext="http://example.com/{x}".format(x=i)
            )
            article = models.Article(**source)
            article.save(blocking=i == article_count - 1)

        app.config["DISCOVERY_RECORDS_PER_FILE"] = batch_size

        if tmp_write_arg == "fail":
            app.config["STORE_TMP_IMPL"] = StoreMockFactory.no_writes_classpath()

        if store_write_arg == "fail":
            app.config["STORE_IMPL"] = StoreMockFactory.no_writes_classpath()

        ###########################################################
        # Execution

        job = PublicDataDumpBackgroundTask.prepare("testuser", clean=clean, prune=prune, types=types)
        task = PublicDataDumpBackgroundTask(job)
        BackgroundApi.execute(task)

        # make sure we have a fresh copy of the job
        job = task.background_job
        assert job.status == status_arg

        if job.status != "error":
            article_url = models.Cache.get_public_data_dump("article")
            journal_url = models.Cache.get_public_data_dump("journal")

            assert article_url is not None
            assert journal_url is not None

            assert localStore.exists(container_id)

            files = localStore.list(container_id)
            assert len(files) == 2

            day_at_start = dates.today()
            article_file = "doaj_article_data_" + day_at_start + ".tar.gz"
            journal_file = "doaj_journal_data_" + day_at_start + ".tar.gz"
            assert article_file in files
            assert journal_file in files



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

import os, shutil, tarfile, json
from io import StringIO

def load_cases():
    return load_parameter_sets(rel2abs(__file__, "..", "matrices", "tasks.public_data_dump"), "data_dump", "test_id",
                               {"test_id" : []})


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

        models.cache.Cache = ModelCacheMockFactory.in_memory()

    def tearDown(self):
        app.config["STORE_TMP_IMPL"] = self.store_tmp_imp
        app.config["STORE_IMPL"] = self.store_imp
        app.config["DISCOVERY_RECORDS_PER_FILE"] = self.discovery_records_per_file

        shutil.rmtree(rel2abs(__file__, "..", "tmp"))
        app.config["STORE_LOCAL_DIR"] = self.store_local_dir
        app.config["STORE_TMP_DIR"] = self.store_tmp_dir

        models.cache.Cache = self.cache

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

        journal_count = int(journals_arg)
        article_count = int(articles_arg)
        batch_size = int(batch_size_arg)
        journal_file_count = 0 if journal_count == 0 else (journal_count // batch_size) + 1
        article_file_count = 0 if article_count == 0 else (article_count // batch_size) + 1
        first_article_file_records = 0 if article_count == 0 else batch_size if article_count > batch_size else article_count
        first_journal_file_records = 0 if journal_count == 0 else batch_size if journal_count > batch_size else journal_count

        # add the data to the index first, to maximise the time it has to become available for search
        sources = JournalFixtureFactory.make_many_journal_sources(journal_count, in_doaj=True)
        jids = []
        for i in range(len(sources)):
            source = sources[i]
            journal = models.Journal(**source)
            journal.save()
            jids.append((journal.id, journal.last_updated))

        aids = []
        for i in range(article_count):
            source = ArticleFixtureFactory.make_article_source(
                eissn="{x}000-0000".format(x=i),
                pissn="0000-{x}000".format(x=i),
                with_id=False,
                doi="10.123/{x}".format(x=i),
                fulltext="http://example.com/{x}".format(x=i)
            )
            article = models.Article(**source)
            article.save()
            aids.append((article.id, article.last_updated))

        # construct some test data in the local store
        container_id = app.config["STORE_PUBLIC_DATA_DUMP_CONTAINER"]
        localStore = store.StoreLocal(None)
        localStoreFiles = []
        if clean or prune:
            for i in range(5):
                localStore.store(container_id, "doaj_article_data_2018-01-0" + str(i) + ".tar.gz",
                                 source_stream=StringIO("test"))
                localStore.store(container_id, "doaj_journal_data_2018-01-0" + str(i) + ".tar.gz",
                                 source_stream=StringIO("test"))
            localStoreFiles = localStore.list(container_id)

        app.config["DISCOVERY_RECORDS_PER_FILE"] = batch_size

        # set the mocks for store write failures
        if tmp_write_arg == "fail":
            app.config["STORE_TMP_IMPL"] = StoreMockFactory.no_writes_classpath()

        if store_write_arg == "fail":
            app.config["STORE_IMPL"] = StoreMockFactory.no_writes_classpath()

        # block until all the records are saved
        for jid, lu in jids:
            models.Journal.block(jid, lu, sleep=0.05)
        for aid, lu in aids:
            models.Article.block(aid, lu, sleep=0.05)

        ###########################################################
        # Execution

        job = PublicDataDumpBackgroundTask.prepare("testuser", clean=clean, prune=prune, types=types)
        task = PublicDataDumpBackgroundTask(job)
        BackgroundApi.execute(task)

        # make sure we have a fresh copy of the job
        job = task.background_job
        assert job.status == status_arg

        if job.status != "error":
            article_url = models.cache.Cache.get_public_data_dump().get("article", {}).get("url")
            if types_arg in ["-", "all", "article"]:
                assert article_url is not None
            else:
                assert article_url is None

            journal_url = models.cache.Cache.get_public_data_dump().get("journal", {}).get("url")
            if types_arg in ["-", "all", "journal"]:
                assert journal_url is not None
            else:
                assert journal_url is None

            assert localStore.exists(container_id)
            files = localStore.list(container_id)

            if types_arg in ["-", "all"]:
                assert len(files) == 2
            else:
                assert len(files) == 1

            day_at_start = dates.today()

            if types_arg in ["-", "all", "article"]:
                article_file = "doaj_article_data_" + day_at_start + ".tar.gz"
                assert article_file in files

                stream = localStore.get(container_id, article_file)
                tarball = tarfile.open(fileobj=stream, mode="r:gz")
                members = tarball.getmembers()
                assert len(members) == article_file_count

                if len(members) > 0:
                    f = tarball.extractfile(members[0])
                    data = json.loads(f.read().decode("utf-8"))
                    assert len(data) == first_article_file_records

                    record = data[0]
                    for key in list(record.keys()):
                        assert key in ["admin", "bibjson", "id", "last_updated", "created_date"]
                    if "admin" in record:
                        for key in list(record["admin"].keys()):
                            assert key in ["ticked", "seal"]

            if types_arg in ["-", "all", "journal"]:
                journal_file = "doaj_journal_data_" + day_at_start + ".tar.gz"
                assert journal_file in files

                stream = localStore.get(container_id, journal_file)
                tarball = tarfile.open(fileobj=stream, mode="r:gz")
                members = tarball.getmembers()
                assert len(members) == journal_file_count

                if len(members) > 0:
                    f = tarball.extractfile(members[0])
                    data = json.loads(f.read().decode("utf-8"))
                    assert len(data) == first_journal_file_records

                    record = data[0]
                    for key in list(record.keys()):
                        assert key in ["admin", "bibjson", "id", "last_updated", "created_date"]
                    if "admin" in record:
                        for key in list(record["admin"].keys()):
                            assert key in ["ticked", "seal"]

        else:
            # in the case of an error, we expect the tmp store to have been cleaned up
            tmpStore = store.TempStore()
            assert not tmpStore.exists(container_id)

            # in the case of an error, we expect the main store not to have been touched
            # (for the errors that we are checking for)
            if prune and not clean:
                # no matter what the error, if we didn't specify clean then we expect everything
                # to survive
                survived = localStore.list(container_id)
                assert localStoreFiles == survived
            elif clean:
                # if we specified clean, then it's possible the main store was cleaned before the
                # error occurred, in which case it depends on the error.  This reminds us that
                # clean shouldn't be used in production
                if tmp_write_arg == "fail":
                    assert not localStore.exists(container_id)
                else:
                    survived = localStore.list(container_id)
                    assert localStoreFiles == survived
            else:
                # otherwise, we expect the main store to have survived
                assert not localStore.exists(container_id)
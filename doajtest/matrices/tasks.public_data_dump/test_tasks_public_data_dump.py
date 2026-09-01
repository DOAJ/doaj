import json
import tarfile
from io import StringIO

from combinatrix.testintegration import load_parameter_sets
from parameterized import parameterized

from doajtest import helpers
from doajtest.fixtures import JournalFixtureFactory, ArticleFixtureFactory
from doajtest.helpers import DoajTestCase
from doajtest.mocks.store import StoreMockFactory
from lib.thread_utils import wait_until
from portality import models, store
from portality.background import BackgroundApi
from portality.core import app
from portality.lib import dates
from portality.lib.paths import rel2abs
from portality.tasks.public_data_dump import PublicDataDumpBackgroundTask
from portality.bll import DOAJ


class TestPublicDataDumpTask(DoajTestCase):

    def setUp(self):
        super(TestPublicDataDumpTask, self).setUp()

        self.discovery_records_per_file = app.config.get("DISCOVERY_RECORDS_PER_FILE")
        self.store_local_patcher = helpers.StoreLocalPatcher()
        self.store_local_patcher.setUp(self.app_test)
        self.svc = DOAJ.publicDataDumpService()


    def tearDown(self):
        app.config["DISCOVERY_RECORDS_PER_FILE"] = self.discovery_records_per_file
        self.store_local_patcher.tearDown(self.app_test)
        super(TestPublicDataDumpTask, self).tearDown()

    def run_test(self, kwargs):
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
                localStore.store(container_id, "doaj_article_data_2018-01-0" + str(i + 1) + ".tar.gz",
                                 source_stream=StringIO("test"))
                localStore.store(container_id, "doaj_journal_data_2018-01-0" + str(i + 1) + ".tar.gz",
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
            wait_until(lambda: self.svc.get_premium_dump() is not None)
            record = self.svc.get_premium_dump()
            article_url = record.article_url
            if types_arg in ["-", "all", "article"]:
                assert article_url is not None
            else:
                assert article_url is None

            journal_url = record.journal_url
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
                            assert key in ["ticked"]

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
                            assert key in ["ticked"]

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

    def test_001(self):
        self.run_test({'clean': 'yes', 'prune': 'yes', 'types': 'all', 'journals': '0', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '1'})
        
    def test_002(self):
        self.run_test({'clean': 'yes', 'prune': 'yes', 'types': 'all', 'journals': '0', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'fail', 'status': 'error', 'test_id': '2'})
        
    def test_003(self):
        self.run_test({'clean': 'yes', 'prune': 'yes', 'types': 'all', 'journals': '0', 'articles': '0', 'batch_size': '3', 'tmp_write': 'fail', 'store_write': 'success', 'status': 'error', 'test_id': '3'})
        
    def test_004(self):
        self.run_test({'clean': 'yes', 'prune': 'yes', 'types': 'all', 'journals': '0', 'articles': '2', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '4'})
        
    def test_005(self):
        self.run_test({'clean': 'yes', 'prune': 'yes', 'types': 'all', 'journals': '0', 'articles': '2', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'fail', 'status': 'error', 'test_id': '5'})
        
    def test_006(self):
        self.run_test({'clean': 'yes', 'prune': 'yes', 'types': 'all', 'journals': '0', 'articles': '2', 'batch_size': '3', 'tmp_write': 'fail', 'store_write': 'success', 'status': 'error', 'test_id': '6'})
        
    def test_007(self):
        self.run_test({'clean': 'yes', 'prune': 'yes', 'types': 'all', 'journals': '0', 'articles': '4', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '7'})
        
    def test_008(self):
        self.run_test({'clean': 'yes', 'prune': 'yes', 'types': 'all', 'journals': '0', 'articles': '4', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'fail', 'status': 'error', 'test_id': '8'})
        
    def test_009(self):
        self.run_test({'clean': 'yes', 'prune': 'yes', 'types': 'all', 'journals': '0', 'articles': '4', 'batch_size': '3', 'tmp_write': 'fail', 'store_write': 'success', 'status': 'error', 'test_id': '9'})
        
    def test_010(self):
        self.run_test({'clean': 'yes', 'prune': 'yes', 'types': 'all', 'journals': '2', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '10'})
        
    def test_011(self):
        self.run_test({'clean': 'yes', 'prune': 'yes', 'types': 'all', 'journals': '2', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'fail', 'status': 'error', 'test_id': '11'})
        
    def test_012(self):
        self.run_test({'clean': 'yes', 'prune': 'yes', 'types': 'all', 'journals': '2', 'articles': '0', 'batch_size': '3', 'tmp_write': 'fail', 'store_write': 'success', 'status': 'error', 'test_id': '12'})
        
    def test_013(self):
        self.run_test({'clean': 'yes', 'prune': 'yes', 'types': 'all', 'journals': '2', 'articles': '2', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '13'})
        
    def test_014(self):
        self.run_test({'clean': 'yes', 'prune': 'yes', 'types': 'all', 'journals': '2', 'articles': '2', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'fail', 'status': 'error', 'test_id': '14'})
        
    def test_015(self):
        self.run_test({'clean': 'yes', 'prune': 'yes', 'types': 'all', 'journals': '2', 'articles': '2', 'batch_size': '3', 'tmp_write': 'fail', 'store_write': 'success', 'status': 'error', 'test_id': '15'})
        
    def test_016(self):
        self.run_test({'clean': 'yes', 'prune': 'yes', 'types': 'all', 'journals': '2', 'articles': '4', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '16'})
        
    def test_017(self):
        self.run_test({'clean': 'yes', 'prune': 'yes', 'types': 'all', 'journals': '2', 'articles': '4', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'fail', 'status': 'error', 'test_id': '17'})
        
    def test_018(self):
        self.run_test({'clean': 'yes', 'prune': 'yes', 'types': 'all', 'journals': '2', 'articles': '4', 'batch_size': '3', 'tmp_write': 'fail', 'store_write': 'success', 'status': 'error', 'test_id': '18'})
        
    def test_019(self):
        self.run_test({'clean': 'yes', 'prune': 'yes', 'types': 'all', 'journals': '4', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '19'})
        
    def test_020(self):
        self.run_test({'clean': 'yes', 'prune': 'yes', 'types': 'all', 'journals': '4', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'fail', 'status': 'error', 'test_id': '20'})
        
    def test_021(self):
        self.run_test({'clean': 'yes', 'prune': 'yes', 'types': 'all', 'journals': '4', 'articles': '0', 'batch_size': '3', 'tmp_write': 'fail', 'store_write': 'success', 'status': 'error', 'test_id': '21'})
        
    def test_022(self):
        self.run_test({'clean': 'yes', 'prune': 'yes', 'types': 'all', 'journals': '4', 'articles': '2', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '22'})
        
    def test_023(self):
        self.run_test({'clean': 'yes', 'prune': 'yes', 'types': 'all', 'journals': '4', 'articles': '2', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'fail', 'status': 'error', 'test_id': '23'})
        
    def test_024(self):
        self.run_test({'clean': 'yes', 'prune': 'yes', 'types': 'all', 'journals': '4', 'articles': '2', 'batch_size': '3', 'tmp_write': 'fail', 'store_write': 'success', 'status': 'error', 'test_id': '24'})
        
    def test_025(self):
        self.run_test({'clean': 'yes', 'prune': 'yes', 'types': 'all', 'journals': '4', 'articles': '4', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '25'})
        
    def test_026(self):
        self.run_test({'clean': 'yes', 'prune': 'yes', 'types': 'all', 'journals': '4', 'articles': '4', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'fail', 'status': 'error', 'test_id': '26'})
        
    def test_027(self):
        self.run_test({'clean': 'yes', 'prune': 'yes', 'types': 'all', 'journals': '4', 'articles': '4', 'batch_size': '3', 'tmp_write': 'fail', 'store_write': 'success', 'status': 'error', 'test_id': '27'})
        
    def test_028(self):
        self.run_test({'clean': 'yes', 'prune': 'yes', 'types': 'journal', 'journals': '0', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '28'})
        
    def test_029(self):
        self.run_test({'clean': 'yes', 'prune': 'yes', 'types': 'journal', 'journals': '0', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'fail', 'status': 'error', 'test_id': '29'})
        
    def test_030(self):
        self.run_test({'clean': 'yes', 'prune': 'yes', 'types': 'journal', 'journals': '0', 'articles': '0', 'batch_size': '3', 'tmp_write': 'fail', 'store_write': 'success', 'status': 'error', 'test_id': '30'})
        
    def test_031(self):
        self.run_test({'clean': 'yes', 'prune': 'yes', 'types': 'journal', 'journals': '2', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '31'})
        
    def test_032(self):
        self.run_test({'clean': 'yes', 'prune': 'yes', 'types': 'journal', 'journals': '2', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'fail', 'status': 'error', 'test_id': '32'})
        
    def test_033(self):
        self.run_test({'clean': 'yes', 'prune': 'yes', 'types': 'journal', 'journals': '2', 'articles': '0', 'batch_size': '3', 'tmp_write': 'fail', 'store_write': 'success', 'status': 'error', 'test_id': '33'})
        
    def test_034(self):
        self.run_test({'clean': 'yes', 'prune': 'yes', 'types': 'journal', 'journals': '4', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '34'})
        
    def test_035(self):
        self.run_test({'clean': 'yes', 'prune': 'yes', 'types': 'journal', 'journals': '4', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'fail', 'status': 'error', 'test_id': '35'})
        
    def test_036(self):
        self.run_test({'clean': 'yes', 'prune': 'yes', 'types': 'journal', 'journals': '4', 'articles': '0', 'batch_size': '3', 'tmp_write': 'fail', 'store_write': 'success', 'status': 'error', 'test_id': '36'})
        
    def test_037(self):
        self.run_test({'clean': 'yes', 'prune': 'yes', 'types': 'article', 'journals': '0', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '37'})
        
    def test_038(self):
        self.run_test({'clean': 'yes', 'prune': 'yes', 'types': 'article', 'journals': '0', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'fail', 'status': 'error', 'test_id': '38'})
        
    def test_039(self):
        self.run_test({'clean': 'yes', 'prune': 'yes', 'types': 'article', 'journals': '0', 'articles': '0', 'batch_size': '3', 'tmp_write': 'fail', 'store_write': 'success', 'status': 'error', 'test_id': '39'})
        
    def test_040(self):
        self.run_test({'clean': 'yes', 'prune': 'yes', 'types': 'article', 'journals': '0', 'articles': '2', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '40'})
        
    def test_041(self):
        self.run_test({'clean': 'yes', 'prune': 'yes', 'types': 'article', 'journals': '0', 'articles': '2', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'fail', 'status': 'error', 'test_id': '41'})
        
    def test_042(self):
        self.run_test({'clean': 'yes', 'prune': 'yes', 'types': 'article', 'journals': '0', 'articles': '2', 'batch_size': '3', 'tmp_write': 'fail', 'store_write': 'success', 'status': 'error', 'test_id': '42'})
        
    def test_043(self):
        self.run_test({'clean': 'yes', 'prune': 'yes', 'types': 'article', 'journals': '0', 'articles': '4', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '43'})
        
    def test_044(self):
        self.run_test({'clean': 'yes', 'prune': 'yes', 'types': 'article', 'journals': '0', 'articles': '4', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'fail', 'status': 'error', 'test_id': '44'})
        
    def test_045(self):
        self.run_test({'clean': 'yes', 'prune': 'yes', 'types': 'article', 'journals': '0', 'articles': '4', 'batch_size': '3', 'tmp_write': 'fail', 'store_write': 'success', 'status': 'error', 'test_id': '45'})
        
    def test_046(self):
        self.run_test({'clean': 'yes', 'prune': 'yes', 'types': '-', 'journals': '0', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '46'})
        
    def test_047(self):
        self.run_test({'clean': 'yes', 'prune': 'no', 'types': 'all', 'journals': '0', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '47'})
        
    def test_048(self):
        self.run_test({'clean': 'yes', 'prune': 'no', 'types': 'all', 'journals': '0', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'fail', 'status': 'error', 'test_id': '48'})
        
    def test_049(self):
        self.run_test({'clean': 'yes', 'prune': 'no', 'types': 'all', 'journals': '0', 'articles': '0', 'batch_size': '3', 'tmp_write': 'fail', 'store_write': 'success', 'status': 'error', 'test_id': '49'})
        
    def test_050(self):
        self.run_test({'clean': 'yes', 'prune': 'no', 'types': 'all', 'journals': '0', 'articles': '2', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '50'})
        
    def test_051(self):
        self.run_test({'clean': 'yes', 'prune': 'no', 'types': 'all', 'journals': '0', 'articles': '2', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'fail', 'status': 'error', 'test_id': '51'})
        
    def test_052(self):
        self.run_test({'clean': 'yes', 'prune': 'no', 'types': 'all', 'journals': '0', 'articles': '2', 'batch_size': '3', 'tmp_write': 'fail', 'store_write': 'success', 'status': 'error', 'test_id': '52'})
        
    def test_053(self):
        self.run_test({'clean': 'yes', 'prune': 'no', 'types': 'all', 'journals': '0', 'articles': '4', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '53'})
        
    def test_054(self):
        self.run_test({'clean': 'yes', 'prune': 'no', 'types': 'all', 'journals': '0', 'articles': '4', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'fail', 'status': 'error', 'test_id': '54'})
        
    def test_055(self):
        self.run_test({'clean': 'yes', 'prune': 'no', 'types': 'all', 'journals': '0', 'articles': '4', 'batch_size': '3', 'tmp_write': 'fail', 'store_write': 'success', 'status': 'error', 'test_id': '55'})
        
    def test_056(self):
        self.run_test({'clean': 'yes', 'prune': 'no', 'types': 'all', 'journals': '2', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '56'})
        
    def test_057(self):
        self.run_test({'clean': 'yes', 'prune': 'no', 'types': 'all', 'journals': '2', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'fail', 'status': 'error', 'test_id': '57'})
        
    def test_058(self):
        self.run_test({'clean': 'yes', 'prune': 'no', 'types': 'all', 'journals': '2', 'articles': '0', 'batch_size': '3', 'tmp_write': 'fail', 'store_write': 'success', 'status': 'error', 'test_id': '58'})
        
    def test_059(self):
        self.run_test({'clean': 'yes', 'prune': 'no', 'types': 'all', 'journals': '2', 'articles': '2', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '59'})
        
    def test_060(self):
        self.run_test({'clean': 'yes', 'prune': 'no', 'types': 'all', 'journals': '2', 'articles': '2', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'fail', 'status': 'error', 'test_id': '60'})
        
    def test_061(self):
        self.run_test({'clean': 'yes', 'prune': 'no', 'types': 'all', 'journals': '2', 'articles': '2', 'batch_size': '3', 'tmp_write': 'fail', 'store_write': 'success', 'status': 'error', 'test_id': '61'})
        
    def test_062(self):
        self.run_test({'clean': 'yes', 'prune': 'no', 'types': 'all', 'journals': '2', 'articles': '4', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '62'})
        
    def test_063(self):
        self.run_test({'clean': 'yes', 'prune': 'no', 'types': 'all', 'journals': '2', 'articles': '4', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'fail', 'status': 'error', 'test_id': '63'})
        
    def test_064(self):
        self.run_test({'clean': 'yes', 'prune': 'no', 'types': 'all', 'journals': '2', 'articles': '4', 'batch_size': '3', 'tmp_write': 'fail', 'store_write': 'success', 'status': 'error', 'test_id': '64'})
        
    def test_065(self):
        self.run_test({'clean': 'yes', 'prune': 'no', 'types': 'all', 'journals': '4', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '65'})
        
    def test_066(self):
        self.run_test({'clean': 'yes', 'prune': 'no', 'types': 'all', 'journals': '4', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'fail', 'status': 'error', 'test_id': '66'})
        
    def test_067(self):
        self.run_test({'clean': 'yes', 'prune': 'no', 'types': 'all', 'journals': '4', 'articles': '0', 'batch_size': '3', 'tmp_write': 'fail', 'store_write': 'success', 'status': 'error', 'test_id': '67'})
        
    def test_068(self):
        self.run_test({'clean': 'yes', 'prune': 'no', 'types': 'all', 'journals': '4', 'articles': '2', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '68'})
        
    def test_069(self):
        self.run_test({'clean': 'yes', 'prune': 'no', 'types': 'all', 'journals': '4', 'articles': '2', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'fail', 'status': 'error', 'test_id': '69'})
        
    def test_070(self):
        self.run_test({'clean': 'yes', 'prune': 'no', 'types': 'all', 'journals': '4', 'articles': '2', 'batch_size': '3', 'tmp_write': 'fail', 'store_write': 'success', 'status': 'error', 'test_id': '70'})
        
    def test_071(self):
        self.run_test({'clean': 'yes', 'prune': 'no', 'types': 'all', 'journals': '4', 'articles': '4', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '71'})
        
    def test_072(self):
        self.run_test({'clean': 'yes', 'prune': 'no', 'types': 'all', 'journals': '4', 'articles': '4', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'fail', 'status': 'error', 'test_id': '72'})
        
    def test_073(self):
        self.run_test({'clean': 'yes', 'prune': 'no', 'types': 'all', 'journals': '4', 'articles': '4', 'batch_size': '3', 'tmp_write': 'fail', 'store_write': 'success', 'status': 'error', 'test_id': '73'})
        
    def test_074(self):
        self.run_test({'clean': 'yes', 'prune': 'no', 'types': 'journal', 'journals': '0', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '74'})
        
    def test_075(self):
        self.run_test({'clean': 'yes', 'prune': 'no', 'types': 'journal', 'journals': '0', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'fail', 'status': 'error', 'test_id': '75'})
        
    def test_076(self):
        self.run_test({'clean': 'yes', 'prune': 'no', 'types': 'journal', 'journals': '0', 'articles': '0', 'batch_size': '3', 'tmp_write': 'fail', 'store_write': 'success', 'status': 'error', 'test_id': '76'})
        
    def test_077(self):
        self.run_test({'clean': 'yes', 'prune': 'no', 'types': 'journal', 'journals': '2', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '77'})
        
    def test_078(self):
        self.run_test({'clean': 'yes', 'prune': 'no', 'types': 'journal', 'journals': '2', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'fail', 'status': 'error', 'test_id': '78'})
        
    def test_079(self):
        self.run_test({'clean': 'yes', 'prune': 'no', 'types': 'journal', 'journals': '2', 'articles': '0', 'batch_size': '3', 'tmp_write': 'fail', 'store_write': 'success', 'status': 'error', 'test_id': '79'})
        
    def test_080(self):
        self.run_test({'clean': 'yes', 'prune': 'no', 'types': 'journal', 'journals': '4', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '80'})
        
    def test_081(self):
        self.run_test({'clean': 'yes', 'prune': 'no', 'types': 'journal', 'journals': '4', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'fail', 'status': 'error', 'test_id': '81'})
        
    def test_082(self):
        self.run_test({'clean': 'yes', 'prune': 'no', 'types': 'journal', 'journals': '4', 'articles': '0', 'batch_size': '3', 'tmp_write': 'fail', 'store_write': 'success', 'status': 'error', 'test_id': '82'})
        
    def test_083(self):
        self.run_test({'clean': 'yes', 'prune': 'no', 'types': 'article', 'journals': '0', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '83'})
        
    def test_084(self):
        self.run_test({'clean': 'yes', 'prune': 'no', 'types': 'article', 'journals': '0', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'fail', 'status': 'error', 'test_id': '84'})
        
    def test_085(self):
        self.run_test({'clean': 'yes', 'prune': 'no', 'types': 'article', 'journals': '0', 'articles': '0', 'batch_size': '3', 'tmp_write': 'fail', 'store_write': 'success', 'status': 'error', 'test_id': '85'})
        
    def test_086(self):
        self.run_test({'clean': 'yes', 'prune': 'no', 'types': 'article', 'journals': '0', 'articles': '2', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '86'})
        
    def test_087(self):
        self.run_test({'clean': 'yes', 'prune': 'no', 'types': 'article', 'journals': '0', 'articles': '2', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'fail', 'status': 'error', 'test_id': '87'})
        
    def test_088(self):
        self.run_test({'clean': 'yes', 'prune': 'no', 'types': 'article', 'journals': '0', 'articles': '2', 'batch_size': '3', 'tmp_write': 'fail', 'store_write': 'success', 'status': 'error', 'test_id': '88'})
        
    def test_089(self):
        self.run_test({'clean': 'yes', 'prune': 'no', 'types': 'article', 'journals': '0', 'articles': '4', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '89'})
        
    def test_090(self):
        self.run_test({'clean': 'yes', 'prune': 'no', 'types': 'article', 'journals': '0', 'articles': '4', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'fail', 'status': 'error', 'test_id': '90'})
        
    def test_091(self):
        self.run_test({'clean': 'yes', 'prune': 'no', 'types': 'article', 'journals': '0', 'articles': '4', 'batch_size': '3', 'tmp_write': 'fail', 'store_write': 'success', 'status': 'error', 'test_id': '91'})
        
    def test_092(self):
        self.run_test({'clean': 'yes', 'prune': 'no', 'types': '-', 'journals': '0', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '92'})
        
    def test_093(self):
        self.run_test({'clean': 'yes', 'prune': '-', 'types': 'all', 'journals': '0', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '93'})
        
    def test_094(self):
        self.run_test({'clean': 'yes', 'prune': '-', 'types': 'journal', 'journals': '0', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '94'})
        
    def test_095(self):
        self.run_test({'clean': 'yes', 'prune': '-', 'types': 'article', 'journals': '0', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '95'})
        
    def test_096(self):
        self.run_test({'clean': 'yes', 'prune': '-', 'types': '-', 'journals': '0', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '96'})
        
    def test_097(self):
        self.run_test({'clean': 'no', 'prune': 'yes', 'types': 'all', 'journals': '0', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '97'})
        
    def test_098(self):
        self.run_test({'clean': 'no', 'prune': 'yes', 'types': 'all', 'journals': '0', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'fail', 'status': 'error', 'test_id': '98'})
        
    def test_099(self):
        self.run_test({'clean': 'no', 'prune': 'yes', 'types': 'all', 'journals': '0', 'articles': '0', 'batch_size': '3', 'tmp_write': 'fail', 'store_write': 'success', 'status': 'error', 'test_id': '99'})
        
    def test_100(self):
        self.run_test({'clean': 'no', 'prune': 'yes', 'types': 'all', 'journals': '0', 'articles': '2', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '100'})
        
    def test_101(self):
        self.run_test({'clean': 'no', 'prune': 'yes', 'types': 'all', 'journals': '0', 'articles': '2', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'fail', 'status': 'error', 'test_id': '101'})
        
    def test_102(self):
        self.run_test({'clean': 'no', 'prune': 'yes', 'types': 'all', 'journals': '0', 'articles': '2', 'batch_size': '3', 'tmp_write': 'fail', 'store_write': 'success', 'status': 'error', 'test_id': '102'})
        
    def test_103(self):
        self.run_test({'clean': 'no', 'prune': 'yes', 'types': 'all', 'journals': '0', 'articles': '4', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '103'})
        
    def test_104(self):
        self.run_test({'clean': 'no', 'prune': 'yes', 'types': 'all', 'journals': '0', 'articles': '4', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'fail', 'status': 'error', 'test_id': '104'})
        
    def test_105(self):
        self.run_test({'clean': 'no', 'prune': 'yes', 'types': 'all', 'journals': '0', 'articles': '4', 'batch_size': '3', 'tmp_write': 'fail', 'store_write': 'success', 'status': 'error', 'test_id': '105'})
        
    def test_106(self):
        self.run_test({'clean': 'no', 'prune': 'yes', 'types': 'all', 'journals': '2', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '106'})
        
    def test_107(self):
        self.run_test({'clean': 'no', 'prune': 'yes', 'types': 'all', 'journals': '2', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'fail', 'status': 'error', 'test_id': '107'})
        
    def test_108(self):
        self.run_test({'clean': 'no', 'prune': 'yes', 'types': 'all', 'journals': '2', 'articles': '0', 'batch_size': '3', 'tmp_write': 'fail', 'store_write': 'success', 'status': 'error', 'test_id': '108'})
        
    def test_109(self):
        self.run_test({'clean': 'no', 'prune': 'yes', 'types': 'all', 'journals': '2', 'articles': '2', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '109'})
        
    def test_110(self):
        self.run_test({'clean': 'no', 'prune': 'yes', 'types': 'all', 'journals': '2', 'articles': '2', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'fail', 'status': 'error', 'test_id': '110'})
        
    def test_111(self):
        self.run_test({'clean': 'no', 'prune': 'yes', 'types': 'all', 'journals': '2', 'articles': '2', 'batch_size': '3', 'tmp_write': 'fail', 'store_write': 'success', 'status': 'error', 'test_id': '111'})
        
    def test_112(self):
        self.run_test({'clean': 'no', 'prune': 'yes', 'types': 'all', 'journals': '2', 'articles': '4', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '112'})
        
    def test_113(self):
        self.run_test({'clean': 'no', 'prune': 'yes', 'types': 'all', 'journals': '2', 'articles': '4', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'fail', 'status': 'error', 'test_id': '113'})
        
    def test_114(self):
        self.run_test({'clean': 'no', 'prune': 'yes', 'types': 'all', 'journals': '2', 'articles': '4', 'batch_size': '3', 'tmp_write': 'fail', 'store_write': 'success', 'status': 'error', 'test_id': '114'})
        
    def test_115(self):
        self.run_test({'clean': 'no', 'prune': 'yes', 'types': 'all', 'journals': '4', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '115'})
        
    def test_116(self):
        self.run_test({'clean': 'no', 'prune': 'yes', 'types': 'all', 'journals': '4', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'fail', 'status': 'error', 'test_id': '116'})
        
    def test_117(self):
        self.run_test({'clean': 'no', 'prune': 'yes', 'types': 'all', 'journals': '4', 'articles': '0', 'batch_size': '3', 'tmp_write': 'fail', 'store_write': 'success', 'status': 'error', 'test_id': '117'})
        
    def test_118(self):
        self.run_test({'clean': 'no', 'prune': 'yes', 'types': 'all', 'journals': '4', 'articles': '2', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '118'})
        
    def test_119(self):
        self.run_test({'clean': 'no', 'prune': 'yes', 'types': 'all', 'journals': '4', 'articles': '2', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'fail', 'status': 'error', 'test_id': '119'})
        
    def test_120(self):
        self.run_test({'clean': 'no', 'prune': 'yes', 'types': 'all', 'journals': '4', 'articles': '2', 'batch_size': '3', 'tmp_write': 'fail', 'store_write': 'success', 'status': 'error', 'test_id': '120'})
        
    def test_121(self):
        self.run_test({'clean': 'no', 'prune': 'yes', 'types': 'all', 'journals': '4', 'articles': '4', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '121'})
        
    def test_122(self):
        self.run_test({'clean': 'no', 'prune': 'yes', 'types': 'all', 'journals': '4', 'articles': '4', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'fail', 'status': 'error', 'test_id': '122'})
        
    def test_123(self):
        self.run_test({'clean': 'no', 'prune': 'yes', 'types': 'all', 'journals': '4', 'articles': '4', 'batch_size': '3', 'tmp_write': 'fail', 'store_write': 'success', 'status': 'error', 'test_id': '123'})
        
    def test_124(self):
        self.run_test({'clean': 'no', 'prune': 'yes', 'types': 'journal', 'journals': '0', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '124'})
        
    def test_125(self):
        self.run_test({'clean': 'no', 'prune': 'yes', 'types': 'journal', 'journals': '0', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'fail', 'status': 'error', 'test_id': '125'})
        
    def test_126(self):
        self.run_test({'clean': 'no', 'prune': 'yes', 'types': 'journal', 'journals': '0', 'articles': '0', 'batch_size': '3', 'tmp_write': 'fail', 'store_write': 'success', 'status': 'error', 'test_id': '126'})
        
    def test_127(self):
        self.run_test({'clean': 'no', 'prune': 'yes', 'types': 'journal', 'journals': '2', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '127'})
        
    def test_128(self):
        self.run_test({'clean': 'no', 'prune': 'yes', 'types': 'journal', 'journals': '2', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'fail', 'status': 'error', 'test_id': '128'})
        
    def test_129(self):
        self.run_test({'clean': 'no', 'prune': 'yes', 'types': 'journal', 'journals': '2', 'articles': '0', 'batch_size': '3', 'tmp_write': 'fail', 'store_write': 'success', 'status': 'error', 'test_id': '129'})
        
    def test_130(self):
        self.run_test({'clean': 'no', 'prune': 'yes', 'types': 'journal', 'journals': '4', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '130'})
        
    def test_131(self):
        self.run_test({'clean': 'no', 'prune': 'yes', 'types': 'journal', 'journals': '4', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'fail', 'status': 'error', 'test_id': '131'})
        
    def test_132(self):
        self.run_test({'clean': 'no', 'prune': 'yes', 'types': 'journal', 'journals': '4', 'articles': '0', 'batch_size': '3', 'tmp_write': 'fail', 'store_write': 'success', 'status': 'error', 'test_id': '132'})
        
    def test_133(self):
        self.run_test({'clean': 'no', 'prune': 'yes', 'types': 'article', 'journals': '0', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '133'})
        
    def test_134(self):
        self.run_test({'clean': 'no', 'prune': 'yes', 'types': 'article', 'journals': '0', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'fail', 'status': 'error', 'test_id': '134'})
        
    def test_135(self):
        self.run_test({'clean': 'no', 'prune': 'yes', 'types': 'article', 'journals': '0', 'articles': '0', 'batch_size': '3', 'tmp_write': 'fail', 'store_write': 'success', 'status': 'error', 'test_id': '135'})
        
    def test_136(self):
        self.run_test({'clean': 'no', 'prune': 'yes', 'types': 'article', 'journals': '0', 'articles': '2', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '136'})
        
    def test_137(self):
        self.run_test({'clean': 'no', 'prune': 'yes', 'types': 'article', 'journals': '0', 'articles': '2', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'fail', 'status': 'error', 'test_id': '137'})
        
    def test_138(self):
        self.run_test({'clean': 'no', 'prune': 'yes', 'types': 'article', 'journals': '0', 'articles': '2', 'batch_size': '3', 'tmp_write': 'fail', 'store_write': 'success', 'status': 'error', 'test_id': '138'})
        
    def test_139(self):
        self.run_test({'clean': 'no', 'prune': 'yes', 'types': 'article', 'journals': '0', 'articles': '4', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '139'})
        
    def test_140(self):
        self.run_test({'clean': 'no', 'prune': 'yes', 'types': 'article', 'journals': '0', 'articles': '4', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'fail', 'status': 'error', 'test_id': '140'})
        
    def test_141(self):
        self.run_test({'clean': 'no', 'prune': 'yes', 'types': 'article', 'journals': '0', 'articles': '4', 'batch_size': '3', 'tmp_write': 'fail', 'store_write': 'success', 'status': 'error', 'test_id': '141'})
        
    def test_142(self):
        self.run_test({'clean': 'no', 'prune': 'yes', 'types': '-', 'journals': '0', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '142'})
        
    def test_143(self):
        self.run_test({'clean': 'no', 'prune': 'no', 'types': 'all', 'journals': '0', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '143'})
        
    def test_144(self):
        self.run_test({'clean': 'no', 'prune': 'no', 'types': 'all', 'journals': '0', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'fail', 'status': 'error', 'test_id': '144'})
        
    def test_145(self):
        self.run_test({'clean': 'no', 'prune': 'no', 'types': 'all', 'journals': '0', 'articles': '0', 'batch_size': '3', 'tmp_write': 'fail', 'store_write': 'success', 'status': 'error', 'test_id': '145'})
        
    def test_146(self):
        self.run_test({'clean': 'no', 'prune': 'no', 'types': 'all', 'journals': '0', 'articles': '2', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '146'})
        
    def test_147(self):
        self.run_test({'clean': 'no', 'prune': 'no', 'types': 'all', 'journals': '0', 'articles': '2', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'fail', 'status': 'error', 'test_id': '147'})
        
    def test_148(self):
        self.run_test({'clean': 'no', 'prune': 'no', 'types': 'all', 'journals': '0', 'articles': '2', 'batch_size': '3', 'tmp_write': 'fail', 'store_write': 'success', 'status': 'error', 'test_id': '148'})
        
    def test_149(self):
        self.run_test({'clean': 'no', 'prune': 'no', 'types': 'all', 'journals': '0', 'articles': '4', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '149'})
        
    def test_150(self):
        self.run_test({'clean': 'no', 'prune': 'no', 'types': 'all', 'journals': '0', 'articles': '4', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'fail', 'status': 'error', 'test_id': '150'})
        
    def test_151(self):
        self.run_test({'clean': 'no', 'prune': 'no', 'types': 'all', 'journals': '0', 'articles': '4', 'batch_size': '3', 'tmp_write': 'fail', 'store_write': 'success', 'status': 'error', 'test_id': '151'})
        
    def test_152(self):
        self.run_test({'clean': 'no', 'prune': 'no', 'types': 'all', 'journals': '2', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '152'})
        
    def test_153(self):
        self.run_test({'clean': 'no', 'prune': 'no', 'types': 'all', 'journals': '2', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'fail', 'status': 'error', 'test_id': '153'})
        
    def test_154(self):
        self.run_test({'clean': 'no', 'prune': 'no', 'types': 'all', 'journals': '2', 'articles': '0', 'batch_size': '3', 'tmp_write': 'fail', 'store_write': 'success', 'status': 'error', 'test_id': '154'})
        
    def test_155(self):
        self.run_test({'clean': 'no', 'prune': 'no', 'types': 'all', 'journals': '2', 'articles': '2', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '155'})
        
    def test_156(self):
        self.run_test({'clean': 'no', 'prune': 'no', 'types': 'all', 'journals': '2', 'articles': '2', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'fail', 'status': 'error', 'test_id': '156'})
        
    def test_157(self):
        self.run_test({'clean': 'no', 'prune': 'no', 'types': 'all', 'journals': '2', 'articles': '2', 'batch_size': '3', 'tmp_write': 'fail', 'store_write': 'success', 'status': 'error', 'test_id': '157'})
        
    def test_158(self):
        self.run_test({'clean': 'no', 'prune': 'no', 'types': 'all', 'journals': '2', 'articles': '4', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '158'})
        
    def test_159(self):
        self.run_test({'clean': 'no', 'prune': 'no', 'types': 'all', 'journals': '2', 'articles': '4', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'fail', 'status': 'error', 'test_id': '159'})
        
    def test_160(self):
        self.run_test({'clean': 'no', 'prune': 'no', 'types': 'all', 'journals': '2', 'articles': '4', 'batch_size': '3', 'tmp_write': 'fail', 'store_write': 'success', 'status': 'error', 'test_id': '160'})
        
    def test_161(self):
        self.run_test({'clean': 'no', 'prune': 'no', 'types': 'all', 'journals': '4', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '161'})
        
    def test_162(self):
        self.run_test({'clean': 'no', 'prune': 'no', 'types': 'all', 'journals': '4', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'fail', 'status': 'error', 'test_id': '162'})
        
    def test_163(self):
        self.run_test({'clean': 'no', 'prune': 'no', 'types': 'all', 'journals': '4', 'articles': '0', 'batch_size': '3', 'tmp_write': 'fail', 'store_write': 'success', 'status': 'error', 'test_id': '163'})
        
    def test_164(self):
        self.run_test({'clean': 'no', 'prune': 'no', 'types': 'all', 'journals': '4', 'articles': '2', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '164'})
        
    def test_165(self):
        self.run_test({'clean': 'no', 'prune': 'no', 'types': 'all', 'journals': '4', 'articles': '2', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'fail', 'status': 'error', 'test_id': '165'})
        
    def test_166(self):
        self.run_test({'clean': 'no', 'prune': 'no', 'types': 'all', 'journals': '4', 'articles': '2', 'batch_size': '3', 'tmp_write': 'fail', 'store_write': 'success', 'status': 'error', 'test_id': '166'})
        
    def test_167(self):
        self.run_test({'clean': 'no', 'prune': 'no', 'types': 'all', 'journals': '4', 'articles': '4', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '167'})
        
    def test_168(self):
        self.run_test({'clean': 'no', 'prune': 'no', 'types': 'all', 'journals': '4', 'articles': '4', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'fail', 'status': 'error', 'test_id': '168'})
        
    def test_169(self):
        self.run_test({'clean': 'no', 'prune': 'no', 'types': 'all', 'journals': '4', 'articles': '4', 'batch_size': '3', 'tmp_write': 'fail', 'store_write': 'success', 'status': 'error', 'test_id': '169'})
        
    def test_170(self):
        self.run_test({'clean': 'no', 'prune': 'no', 'types': 'journal', 'journals': '0', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '170'})
        
    def test_171(self):
        self.run_test({'clean': 'no', 'prune': 'no', 'types': 'journal', 'journals': '0', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'fail', 'status': 'error', 'test_id': '171'})
        
    def test_172(self):
        self.run_test({'clean': 'no', 'prune': 'no', 'types': 'journal', 'journals': '0', 'articles': '0', 'batch_size': '3', 'tmp_write': 'fail', 'store_write': 'success', 'status': 'error', 'test_id': '172'})
        
    def test_173(self):
        self.run_test({'clean': 'no', 'prune': 'no', 'types': 'journal', 'journals': '2', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '173'})
        
    def test_174(self):
        self.run_test({'clean': 'no', 'prune': 'no', 'types': 'journal', 'journals': '2', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'fail', 'status': 'error', 'test_id': '174'})
        
    def test_175(self):
        self.run_test({'clean': 'no', 'prune': 'no', 'types': 'journal', 'journals': '2', 'articles': '0', 'batch_size': '3', 'tmp_write': 'fail', 'store_write': 'success', 'status': 'error', 'test_id': '175'})
        
    def test_176(self):
        self.run_test({'clean': 'no', 'prune': 'no', 'types': 'journal', 'journals': '4', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '176'})
        
    def test_177(self):
        self.run_test({'clean': 'no', 'prune': 'no', 'types': 'journal', 'journals': '4', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'fail', 'status': 'error', 'test_id': '177'})
        
    def test_178(self):
        self.run_test({'clean': 'no', 'prune': 'no', 'types': 'journal', 'journals': '4', 'articles': '0', 'batch_size': '3', 'tmp_write': 'fail', 'store_write': 'success', 'status': 'error', 'test_id': '178'})
        
    def test_179(self):
        self.run_test({'clean': 'no', 'prune': 'no', 'types': 'article', 'journals': '0', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '179'})
        
    def test_180(self):
        self.run_test({'clean': 'no', 'prune': 'no', 'types': 'article', 'journals': '0', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'fail', 'status': 'error', 'test_id': '180'})
        
    def test_181(self):
        self.run_test({'clean': 'no', 'prune': 'no', 'types': 'article', 'journals': '0', 'articles': '0', 'batch_size': '3', 'tmp_write': 'fail', 'store_write': 'success', 'status': 'error', 'test_id': '181'})
        
    def test_182(self):
        self.run_test({'clean': 'no', 'prune': 'no', 'types': 'article', 'journals': '0', 'articles': '2', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '182'})
        
    def test_183(self):
        self.run_test({'clean': 'no', 'prune': 'no', 'types': 'article', 'journals': '0', 'articles': '2', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'fail', 'status': 'error', 'test_id': '183'})
        
    def test_184(self):
        self.run_test({'clean': 'no', 'prune': 'no', 'types': 'article', 'journals': '0', 'articles': '2', 'batch_size': '3', 'tmp_write': 'fail', 'store_write': 'success', 'status': 'error', 'test_id': '184'})
        
    def test_185(self):
        self.run_test({'clean': 'no', 'prune': 'no', 'types': 'article', 'journals': '0', 'articles': '4', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '185'})
        
    def test_186(self):
        self.run_test({'clean': 'no', 'prune': 'no', 'types': 'article', 'journals': '0', 'articles': '4', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'fail', 'status': 'error', 'test_id': '186'})
        
    def test_187(self):
        self.run_test({'clean': 'no', 'prune': 'no', 'types': 'article', 'journals': '0', 'articles': '4', 'batch_size': '3', 'tmp_write': 'fail', 'store_write': 'success', 'status': 'error', 'test_id': '187'})
        
    def test_188(self):
        self.run_test({'clean': 'no', 'prune': 'no', 'types': '-', 'journals': '0', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '188'})
        
    def test_189(self):
        self.run_test({'clean': 'no', 'prune': '-', 'types': 'all', 'journals': '0', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '189'})
        
    def test_190(self):
        self.run_test({'clean': 'no', 'prune': '-', 'types': 'journal', 'journals': '0', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '190'})
        
    def test_191(self):
        self.run_test({'clean': 'no', 'prune': '-', 'types': 'article', 'journals': '0', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '191'})
        
    def test_192(self):
        self.run_test({'clean': 'no', 'prune': '-', 'types': '-', 'journals': '0', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '192'})
        
    def test_193(self):
        self.run_test({'clean': '-', 'prune': 'yes', 'types': 'all', 'journals': '0', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '193'})
        
    def test_194(self):
        self.run_test({'clean': '-', 'prune': 'yes', 'types': 'journal', 'journals': '0', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '194'})
        
    def test_195(self):
        self.run_test({'clean': '-', 'prune': 'yes', 'types': 'article', 'journals': '0', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '195'})
        
    def test_196(self):
        self.run_test({'clean': '-', 'prune': 'yes', 'types': '-', 'journals': '0', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '196'})
        
    def test_197(self):
        self.run_test({'clean': '-', 'prune': 'no', 'types': 'all', 'journals': '0', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '197'})
        
    def test_198(self):
        self.run_test({'clean': '-', 'prune': 'no', 'types': 'journal', 'journals': '0', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '198'})
        
    def test_199(self):
        self.run_test({'clean': '-', 'prune': 'no', 'types': 'article', 'journals': '0', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '199'})
        
    def test_200(self):
        self.run_test({'clean': '-', 'prune': 'no', 'types': '-', 'journals': '0', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '200'})
        
    def test_201(self):
        self.run_test({'clean': '-', 'prune': '-', 'types': 'all', 'journals': '0', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '201'})
        
    def test_202(self):
        self.run_test({'clean': '-', 'prune': '-', 'types': 'journal', 'journals': '0', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '202'})
        
    def test_203(self):
        self.run_test({'clean': '-', 'prune': '-', 'types': 'article', 'journals': '0', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '203'})
        
    def test_204(self):
        self.run_test({'clean': '-', 'prune': '-', 'types': '-', 'journals': '0', 'articles': '0', 'batch_size': '3', 'tmp_write': 'success', 'store_write': 'success', 'status': 'complete', 'test_id': '204'})
        
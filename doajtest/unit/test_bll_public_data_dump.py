from doajtest.fixtures import ArticleFixtureFactory, JournalFixtureFactory, DataDumpFixtureFactory
from doajtest.helpers import DoajTestCase
from portality.lib.thread_utils import wait_until
from portality.models import DataDump, Journal
from portality import constants
from portality.bll import DOAJ
from portality.core import app
from portality.store import StoreFactory
from portality.util import patch_config
from portality.lib import dates
from doajtest.fixtures.store import SludgePump

import tarfile


class TestPublicDataDump(DoajTestCase):

    def logger(self, x):
        self._logs.append(x)

    def setUp(self):
        super(TestPublicDataDump, self).setUp()
        self.old_config = patch_config(app, {
            "DISCOVERY_RECORDS_PER_FILE": 2
        })

        self.articles = ArticleFixtureFactory.make_n_articles(5)
        ArticleFixtureFactory.save_articles(self.articles, block=True)

        self.journals = JournalFixtureFactory.make_n_journals(5)
        JournalFixtureFactory.save_journals(self.journals, block=True)
        self.svc = DOAJ.publicDataDumpService(self.logger)
        self.store = StoreFactory.get(constants.STORE__SCOPE__PUBLIC_DATA_DUMP)
        self._logs = []

    def tearDown(self):
        super(TestPublicDataDump, self).tearDown()
        patch_config(app, self.old_config)
        self.old_config = {}

    def test_01_article_dump(self):
        container, zipped_name, filesize, store_url = self.svc.dump_type(self.svc.ARTICLE)

        assert len(self._logs) > 0
        assert store_url is not None
        assert self.store.size(container, zipped_name) == filesize

        fh = self.store.get(container, zipped_name)
        tar = tarfile.open(fileobj=fh, mode="r:gz")

        files = tar.getnames()
        assert len(files) == 3

    def test_02_journal_dump(self):
        container, zipped_name, filesize, store_url = self.svc.dump_type(self.svc.JOURNAL)

        assert len(self._logs) > 0
        assert store_url is not None
        assert self.store.size(container, zipped_name) == filesize

        fh = self.store.get(container, zipped_name)
        tar = tarfile.open(fileobj=fh, mode="r:gz")

        files = tar.getnames()
        assert len(files) == 3

    def test_03_dump(self):
        dd = self.svc.dump()

        assert isinstance(dd, DataDump)
        assert dd.dump_date is not None

        fh = self.store.get(dd.article_container, dd.article_filename)
        tar = tarfile.open(fileobj=fh, mode="r:gz")
        files = tar.getnames()
        assert len(files) == 3

        fh = self.store.get(dd.journal_container, dd.journal_filename)
        tar = tarfile.open(fileobj=fh, mode="r:gz")
        files = tar.getnames()
        assert len(files) == 3

    def test_04_premium_vs_free(self):
        dds = DataDumpFixtureFactory.make_n_data_dumps(3,
                                                       dump_date=lambda x: dates.format(dates.before_now(86400 if x == 0 else 2505600 if x == 1 else 3456000)),
                                                       journal__filename=lambda x: f"journal_dump_{x + 1}.json",
                                                       article__filename=lambda x: f"article_dump_{x + 1}.json")
        DataDumpFixtureFactory.save_data_dumps(dds, block=True)

        premium = self.svc.get_premium_dump()
        assert premium.id == dds[0].id

        free = self.svc.get_free_dump()
        assert free.id == dds[1].id

        pa = self.svc.get_temporary_url(premium, self.svc.ARTICLE)
        pj = self.svc.get_temporary_url(premium, self.svc.JOURNAL)
        fa = self.svc.get_temporary_url(free, self.svc.ARTICLE)
        fj = self.svc.get_temporary_url(free, self.svc.JOURNAL)

        assert pa is not None
        assert pj is not None
        assert fa is not None
        assert fj is not None

        assert pa != pj
        assert fa != fj
        assert pa != fa
        assert pj != fj

    def test_05_prune(self):
        current_with_files = self.svc.dump()
        DataDumpFixtureFactory.save_data_dumps([current_with_files], block=True)

        # First we want to show that prune on a container with only current data in it has no effect
        container = app.config.get("STORE_PUBLIC_DATA_DUMP_CONTAINER")
        files = self.store.list(container)
        assert len(files) == 2

        self.svc.prune()

        files = self.store.list(container)
        assert len(files) == 2

        # now create more fixtures to demonstrate pruning working effectively
        in_date_without_files = DataDumpFixtureFactory.make_data_dump({"dump_date": dates.format(dates.before_now(86400))})
        in_date_with_files = DataDumpFixtureFactory.make_data_dump({
            "dump_date": dates.format(dates.before_now(86400 * 25)),
            "article": {
                "filename": "article_free.tar.gz"
            },
            "journal": {
                "filename": "journal_free.tar.gz"
            }
        })
        out_of_date_with_file = DataDumpFixtureFactory.make_data_dump({
            "dump_date": dates.format(dates.before_now(86400 * 40)),
            "article": {
                "filename": "article_with_record.tar.gz"
            },
            "journal": {
                "filename": "journal_with_record.tar.gz"
            }
        })

        DataDumpFixtureFactory.save_data_dumps([in_date_without_files, in_date_with_files, out_of_date_with_file], block=True)

        self.store.store(container, "article_without_record.tar.gz", source_stream=SludgePump(1000, format="text"))
        self.store.store(container, "journal_without_record.tar.gz", source_stream=SludgePump(1000, format="text"))
        self.store.store(container, "article_with_record.tar.gz", source_stream=SludgePump(1000, format="text"))
        self.store.store(container, "journal_with_record.tar.gz", source_stream=SludgePump(1000, format="text"))
        self.store.store(container, "article_free.tar.gz", source_stream=SludgePump(1000, format="text"))
        self.store.store(container, "journal_free.tar.gz", source_stream=SludgePump(1000, format="text"))

        # check our fixtures are all correct
        files = self.store.list(container)
        assert len(files) == 8

        records = DataDump.all()
        assert len(records) == 4

        self.svc.prune()

        files = self.store.list(container)
        assert len(files) == 4

        assert current_with_files.article_filename in files
        assert current_with_files.journal_filename in files
        assert in_date_with_files.article_filename in files
        assert in_date_with_files.journal_filename in files

        wait_until(lambda: len(DataDump.all()) == 2)

        records = DataDump.all()
        assert len(records) == 2

        record_ids = [record.id for record in records]
        assert current_with_files.id in record_ids
        assert in_date_with_files.id in record_ids

    def test_07_phase_in(self):
        # 4 data dumps:
        # one from today
        # one from 10 days ago
        # one from 29 days ago
        # one from more than 30 days ago
        dds = DataDumpFixtureFactory.make_n_data_dumps(4,
                                                       dump_date=lambda x: dates.format(dates.before_now(
                                                           0 if x == 0 else 864000 if x == 1 else 2505600 if x == 2 else 3456000)),
                                                       journal__filename=lambda x: f"journal_dump_{x + 1}.json",
                                                       article__filename=lambda x: f"article_dump_{x + 1}.json")
        DataDumpFixtureFactory.save_data_dumps(dds, block=True)

        # normal operation: oldest data dump newer than 30 days
        cfg = patch_config(app, {
            "PREMIUM_PHASE_IN": False,
            "PREMIUM_PHASE_IN_START": dates.before_now(50 * 24 * 60 * 60),
        })
        free = self.svc.get_free_dump()
        assert free.id == dds[2].id

        # 15 days into phase in, oldest dump newer than 15 days
        _ = patch_config(app, {
            "PREMIUM_PHASE_IN": True,
            "PREMIUM_PHASE_IN_START": dates.before_now(15 * 24 * 60 * 60),
        })
        free = self.svc.get_free_dump()
        assert free.id == dds[1].id

        # phase in just started, newest dump
        _ = patch_config(app, {
            "PREMIUM_PHASE_IN": True,
            "PREMIUM_PHASE_IN_START": dates.now()
        })
        free = self.svc.get_free_dump()
        assert free.id == dds[0].id

        patch_config(app, cfg)
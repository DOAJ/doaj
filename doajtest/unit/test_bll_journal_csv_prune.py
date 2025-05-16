from doajtest.fixtures import ArticleFixtureFactory, JournalFixtureFactory, JournalCSVFixtureFactory
from doajtest.helpers import DoajTestCase
from models import JournalCSV
from portality.lib.thread_utils import wait_until
from portality.models import DataDump
from portality import constants
from portality.bll import DOAJ
from portality.core import app
from portality.store import StoreFactory
from portality.util import patch_config
from portality.lib import dates
from doajtest.fixtures.store import SludgePump
from datetime import datetime, timedelta


class TestJournalCSVPrune(DoajTestCase):

    @classmethod
    def setUpClass(cls) -> None:
        super(TestJournalCSVPrune, cls).setUpClass()

    @classmethod
    def tearDownClass(cls) -> None:
        super(TestJournalCSVPrune, cls).tearDownClass()

    def logger(self, x):
        self._logs.append(x)

    def setUp(self):
        super(TestJournalCSVPrune, self).setUp()
        self.old_config = patch_config(app, {
            "DISCOVERY_RECORDS_PER_FILE": 2
        })

        self.articles = ArticleFixtureFactory.make_n_articles(5)
        ArticleFixtureFactory.save_articles(self.articles, block=True)

        self.journals = JournalFixtureFactory.make_n_journals(5)
        JournalFixtureFactory.save_journals(self.journals, block=True)
        self.svc = DOAJ.journalService()
        self.store = StoreFactory.get(constants.STORE__SCOPE__PUBLIC_DATA_DUMP)
        self._logs = []

    def tearDown(self):
        super(TestJournalCSVPrune, self).tearDown()
        patch_config(app, self.old_config)
        self.old_config = {}

    def test_01_prune(self):
        current_with_files = self.svc.csv()
        JournalCSVFixtureFactory.save_journal_csvs([current_with_files], block=True)

        # First we want to show that prune on a container with only current data in it has no effect
        container = app.config.get("STORE_JOURNAL_CSV_CONTAINER")
        files = self.store.list(container)
        assert len(files) == 1

        self.svc.prune_csvs()

        files = self.store.list(container)
        assert len(files) == 1

        # now create more fixtures to demonstrate pruning working effectively
        out_of_date_with_file = JournalCSVFixtureFactory.make_journal_csv({
            "export_date": dates.format(dates.before_now(86400 * 40)),
            "filename": "csv_with_record.csv"
        })
        self.store.store(container, "csv_with_record.csv", source_stream=SludgePump(1000, format="text"))

        yesterday = datetime.now() - timedelta(days=2)
        late = yesterday.replace(hour=15, minute=30, second=0, microsecond=0)
        early = yesterday.replace(hour=10, minute=0, second=0, microsecond=0)

        latest_yesterday = JournalCSVFixtureFactory.make_journal_csv({
            "export_date": dates.format(late),
            "filename": "latest_yesterday.csv"
        })
        self.store.store(container, "latest_yesterday.csv", source_stream=SludgePump(1000, format="text"))

        early_yesterday = JournalCSVFixtureFactory.make_journal_csv({
            "export_date": dates.format(early),
            "filename": "early_yesterday.csv"
        })
        self.store.store(container, "early_yesterday.csv", source_stream=SludgePump(1000, format="text"))

        in_date_without_files = JournalCSVFixtureFactory.make_journal_csv({"export_date": dates.format(dates.before_now(86400 * 5))})
        in_date_with_files = JournalCSVFixtureFactory.make_journal_csv({
            "export_date": dates.format(dates.before_now(86400 * 10)),
            "filename": "in_date_with_files.csv"
        })
        self.store.store(container, "in_date_with_files.csv", source_stream=SludgePump(1000, format="text"))

        self.store.store(container, "no_record.csv", source_stream=SludgePump(1000, format="text"))

        JournalCSVFixtureFactory.save_journal_csvs([
            out_of_date_with_file,
            latest_yesterday,
            early_yesterday,
            in_date_without_files,
            in_date_with_files,
            out_of_date_with_file
        ], block=True)

        # check our fixtures are all correct
        files = self.store.list(container)
        assert len(files) == 6

        records = JournalCSV.all()
        assert len(records) == 6

        self.svc.prune_csvs()

        files = self.store.list(container)
        assert len(files) == 3

        assert current_with_files.filename in files
        assert latest_yesterday.filename in files
        assert in_date_with_files.filename in files

        wait_until(lambda: len(JournalCSV.all()) == 2)

        records = JournalCSV.all()
        assert len(records) == 3

        record_ids = [record.id for record in records]
        assert current_with_files.id in record_ids
        assert latest_yesterday.id in record_ids
        assert in_date_with_files.id in record_ids

    def test_02_premium_vs_free(self):
        dds = JournalCSVFixtureFactory.make_n_csvs(3,
                                                       export_date=lambda x: dates.format(dates.before_now(86400 if x == 0 else 2505600 if x == 1 else 3456000)),
                                                       filename=lambda x: f"journal_csv_{x + 1}.json")
        JournalCSVFixtureFactory.save_journal_csvs(dds, block=True)

        premium = self.svc.get_premium_csv()
        assert premium.id == dds[0].id

        free = self.svc.get_free_csv()
        assert free.id == dds[1].id

        tp = self.svc.get_temporary_url(premium)
        tf = self.svc.get_temporary_url(free)

        assert tp is not None
        assert tf is not None
        assert tp != tf

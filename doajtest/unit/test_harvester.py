import time

from doajtest.fixtures import AccountFixtureFactory, JournalFixtureFactory, ArticleFixtureFactory
from doajtest.fixtures.harvester import HarvestStateFactory, EPMCFixtureFactory
from doajtest.helpers import DoajTestCase
from portality.api.v2.client.client import DOAJv1API
from portality.core import app
from portality.tasks.harvester import HarvesterBackgroundTask
from portality import models
from portality.api.v2.client import client as doajclient
from portality.tasks.harvester_helpers import workflow
from portality.tasks.harvester_helpers.workflow import HarvesterWorkflow
from portality.models.harvester import HarvestState
from portality.models.harvester import HarvesterPlugin

class TestHarvester(DoajTestCase):

    def mock_get_journals_issns(self, string1):
        return ["1234-5678", "9876-5432"]

    def mock_harvest_find_by_issn(self, account, issns):
        return HarvestStateFactory.harvest_state()

    def mock_EuropePMC_complex_search_iterator(self, query, throttle):
        return EPMCFixtureFactory.epmc_metadata()

    def setUp(self):
        self.complex_search_iterator_old = EPMCFixtureFactory.epmc_metadata
        EPMCFixtureFactory.epmc_metadata = self.mock_EuropePMC_complex_search_iterator
        self.get_journals_issns_old = HarvesterWorkflow.get_journals_issns
        HarvesterWorkflow.get_journals_issns = self.mock_get_journals_issns
        self.old_harvest_find_by_issn = HarvestState.find_by_issn
        HarvestState.find_by_issn = self.mock_harvest_find_by_issn
        self.publisher = models.Account(**AccountFixtureFactory.make_publisher_source())
        self.journal = models.Journal(**JournalFixtureFactory.make_journal_source())
        self.publisher.add_journal(self.journal.id)
        self.publisher.generate_api_key()

        self.publisher.save()
        self.journal.save()
        time.sleep(2)

        # self.old_harvesters = app.config.get('HARVESTERS')
        # app.config['HARVESTERS'] = "harvesters"
        self.old_harvester_api_keys = app.config.get('HARVESTER_API_KEYS')
        # app.config['HARVESTER_API_KEYS'] = {self.publisher.id: self.publisher.api_key}

        self.article_correct = models.Article(**ArticleFixtureFactory.make_article_source("1234-5678", "9876-5432"))
        self.article_incorrect = models.Article(**ArticleFixtureFactory.make_article_source("1111-1111", "2222-2222"))

    def tearDown(self):
        # app.config['HARVESTERS'] = self.old_harvesters
        app.config['HARVESTER_API_KEYS'] = self.old_harvester_api_keys
        HarvesterWorkflow.get_journals_issns = self.get_journals_issns_old
        HarvestState.find_by_issn = self.old_harvest_find_by_issn
        EPMCFixtureFactory.epmc_metadata = self.complex_search_iterator_old

    def test_harvest(self):
        job = models.BackgroundJob()
        task = HarvesterBackgroundTask(job)
        task.run()

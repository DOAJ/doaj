import itertools
import json
import time
from datetime import date, datetime

from unittest.mock import Mock, patch

from doajtest.fixtures import AccountFixtureFactory, JournalFixtureFactory, ArticleFixtureFactory
from doajtest.fixtures.harvester import HarvestStateFactory, EPMCFixtureFactory
from doajtest.helpers import DoajTestCase
from portality.api.v2.client.client import DOAJv1API
from portality.core import app
from portality.tasks.harvester import HarvesterBackgroundTask
from portality import models
from portality.tasks.harvester_helpers.epmc import models as h_models
from portality.lib import httputil
from portality.api.v2.client import client as doajclient
from portality.tasks.harvester_helpers import workflow
from portality.tasks.harvester_helpers.workflow import HarvesterWorkflow
from portality.models.harvester import HarvestState
from portality.models.harvester import HarvesterPlugin


class TestHarvester(DoajTestCase):


    def mock_get_journals_issns(self, string1):
        return ["1234-5678", "9876-5432"]


    def mock_get_url(self, url):
        if url.startswith("https://www.ebi.ac.uk/europepmc"):
            return "blabla"
        else:
            self.old_get(url)

    def setUp(self):
        super(TestHarvester, self).setUp()

        self.get_journals_issns_old = HarvesterWorkflow.get_journals_issns
        HarvesterWorkflow.get_journals_issns = self.mock_get_journals_issns

        self.publisher = models.Account(**AccountFixtureFactory.make_publisher_source())
        self.journal = models.Journal(**JournalFixtureFactory.make_journal_source())
        self.publisher.add_journal(self.journal.id)
        self.publisher.generate_api_key()

        self.publisher.save()
        self.journal.save()
        time.sleep(2)

        self.old_harvester_api_keys = app.config.get('HARVESTER_API_KEYS')
        self.old_initial_harvest_date = app.config.get("INITIAL_HARVEST_DATE")


        app.config['HARVESTER_API_KEYS'] = {self.publisher.id: self.publisher.api_key}

        self.old_get = httputil.get

        today = datetime.today().strftime('%Y-%m-%d')
        app.config["INITIAL_HARVEST_DATE"] = today
        with open('resources/harvester_resp.json') as json_file:
            articles = json.load(json_file)

        articles["request"]["queryString"] = 'ISSN:"1234-5678" OPEN_ACCESS:"y" UPDATE_DATE:' + today + ' sort_date:"y"',
        json_file = open('resources/harvester_resp.json', 'w')
        json.dump(articles, json_file)
        json_file.close()

    def tearDown(self):
        super(TestHarvester, self).tearDown()
        app.config['HARVESTER_API_KEYS'] = self.old_harvester_api_keys
        app.config["INITIAL_HARVEST_DATE"] = self.old_initial_harvest_date
        HarvesterWorkflow.get_journals_issns = self.mock_get_journals_issns

    @patch('portality.tasks.harvester_helpers.epmc.client.EuropePMC.query')
    def test_harvest(self, mock_query):

        with open('resources/harvester_resp.json') as json_file:
            articles = json.load(json_file)

        results = [h_models.EPMCMetadata(r) for r in articles.get("resultList", {}).get("result", [])]
        a = (results, "")
        b = ([], "AoJwgOTOsdfTeDE0ODA4OTIz")
        mock_query.side_effect = itertools.cycle([a, b])

        job = models.BackgroundJob()
        task = HarvesterBackgroundTask(job)
        task.submit(job)

        time.sleep(2)

        articles_saved = [a for a in self.journal.all_articles()]

        assert len(articles_saved) == 1, "expected 1 article, found: {}".format(len(articles))
        assert articles_saved[0].bibjson().title == "Harvester Test Article"


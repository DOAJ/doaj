import itertools
import json
import os
import time
from datetime import date, datetime
from shutil import copyfile

from unittest.mock import Mock, patch

from doajtest.fixtures import AccountFixtureFactory, JournalFixtureFactory, ArticleFixtureFactory
from doajtest.fixtures.harvester import HarvestStateFactory, EPMCFixtureFactory
from doajtest.helpers import DoajTestCase
from portality.api.v2.client.client import DOAJv1API
from portality.core import app
from portality.tasks.harvester import HarvesterBackgroundTask
from portality import models
from portality.tasks.harvester_helpers.epmc import models as h_models
from portality.tasks.harvester_helpers.epmc.client import EuropePMC, EuropePMCException
from portality.tasks.harvester_helpers.epmc.models import EPMCMetadata

RESOURCES = os.path.join(os.path.dirname(os.path.realpath(__file__)), "resources/")

class TestHarvester(DoajTestCase):

    def setUp(self):
        super(TestHarvester, self).setUp()

        self.publisher = models.Account(**AccountFixtureFactory.make_publisher_source())
        self.journal = models.Journal(**JournalFixtureFactory.make_journal_source(True))
        self.publisher.add_journal(self.journal.id)
        self.publisher.generate_api_key()

        self.publisher.save()
        self.journal.save(blocking=True)

        self.old_harvester_api_keys = app.config.get('HARVESTER_API_KEYS')
        self.old_initial_harvest_date = app.config.get("INITIAL_HARVEST_DATE")


        app.config['HARVESTER_API_KEYS'] = {self.publisher.id: self.publisher.api_key}

        today = datetime.today().strftime('%Y-%m-%d')
        app.config["INITIAL_HARVEST_DATE"] = today
        copyfile(RESOURCES + 'harvester_resp.json', RESOURCES + 'harvester_resp_temp.json')
        with open(RESOURCES + 'harvester_resp_temp.json') as json_file:
            articles = json.load(json_file)

        articles["request"]["queryString"] = 'ISSN:"1234-5678" OPEN_ACCESS:"y" UPDATE_DATE:' + today + ' sort_date:"y"',
        json_file = open(RESOURCES + 'harvester_resp_temp.json', 'w')
        json.dump(articles, json_file, indent=4)
        json_file.close()

    def tearDown(self):
        super(TestHarvester, self).tearDown()
        app.config['HARVESTER_API_KEYS'] = self.old_harvester_api_keys
        app.config["INITIAL_HARVEST_DATE"] = self.old_initial_harvest_date
        os.remove(RESOURCES + 'harvester_resp_temp.json')

    @patch('portality.tasks.harvester_helpers.epmc.client.EuropePMC.query')
    def test_harvest(self, mock_query):

        with open('resources/harvester_resp_temp.json') as json_file:
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

        assert len(articles_saved) == 1, "expected 1 article, found: {}".format(len(articles_saved))
        assert articles_saved[0].bibjson().title == "Harvester Test Article"

    @patch('portality.lib.httputil.get')
    def test_query(self, mock_get):

        with open('resources/harvester_resp_temp.json') as json_file:
            articles = json.load(json_file)

        mock_get.return_value.status_code = 401

        job = models.BackgroundJob()
        with self.assertRaises(EuropePMCException):
            EuropePMC().query("query_string")

        mock_get.return_value = None

        with self.assertRaises(EuropePMCException):
            EuropePMC().query("query_string")

        mock_get.return_value = Mock()
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = articles

        result, cursor = EuropePMC().query("query_string")

        assert len(result) == 2
        assert isinstance(result[0], EPMCMetadata)
        assert result[0].journal == "My Journal"
        assert isinstance(result[1], EPMCMetadata)
        assert result[1].journal == "My Journal"






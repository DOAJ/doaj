import itertools
import json
import os
import time
from datetime import datetime

from unittest.mock import Mock, patch

from doajtest.fixtures import AccountFixtureFactory, JournalFixtureFactory
from doajtest.helpers import DoajTestCase, with_es
from portality.core import app
from portality.lib.dates import STD_DATE_FMT
from portality.tasks.harvester import HarvesterBackgroundTask
from portality import models
from portality.tasks.harvester_helpers.epmc import models as h_models
from portality.tasks.harvester_helpers.epmc.client import EuropePMC, EuropePMCException
from portality.tasks.harvester_helpers.epmc.models import EPMCMetadata
from portality.background import BackgroundApi
from portality.lib import dates

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

        self.old_harvest_accounts = app.config.get('HARVEST_ACCOUNTS')
        self.old_initial_harvest_date = app.config.get("INITIAL_HARVEST_DATE")

        app.config['HARVEST_ACCOUNTS'] = [self.publisher.id]

        self.today = datetime.today().strftime(STD_DATE_FMT)
        app.config["INITIAL_HARVEST_DATE"] = self.today

    def tearDown(self):
        super(TestHarvester, self).tearDown()
        app.config['HARVEST_ACCOUNTS'] = self.old_harvest_accounts
        app.config["INITIAL_HARVEST_DATE"] = self.old_initial_harvest_date

    @with_es(indices=[models.Article.__type__, models.Journal.__type__],
             warm_mappings=[models.Article.__type__])
    @patch('portality.tasks.harvester_helpers.epmc.client.EuropePMC.query')
    def test_harvest(self, mock_query):
        # start by adding a zombie background job to prove that this won't hinder the execution of the
        # new job
        zombie = HarvesterBackgroundTask.prepare("testuser")
        zombie.start()
        cd = dates.format(dates.before_now(app.config.get("HARVESTER_ZOMBIE_AGE") * 2))
        zombie.set_created(cd)
        zombie.save(blocking=True)

        with open(os.path.join(RESOURCES, 'harvester_resp.json')) as json_file:
            articles = json.load(json_file)

        articles["request"]["queryString"] = 'ISSN:"1234-5678" OPEN_ACCESS:"y" UPDATE_DATE:' + self.today + ' sort_date:"y"',

        results = [h_models.EPMCMetadata(r) for r in articles.get("resultList", {}).get("result", [])]
        a = (results, "AoJwgOTOsdfTeDE0ODA4OTIz")
        b = ([], "")
        mock_query.side_effect = itertools.cycle([a, b])

        # possible alternative way to execute the job
        job = HarvesterBackgroundTask.prepare("testuser")
        task = HarvesterBackgroundTask(job)
        BackgroundApi.execute(task)

        time.sleep(2)

        print(job.pretty_audit)
        articles_saved = [a for a in self.journal.all_articles()]

        assert len(articles_saved) == 1, "expected 1 article, found: {}".format(len(articles_saved))
        assert articles_saved[0].bibjson().title == "Harvester Test Article"

    @patch('portality.lib.httputil.get')
    def test_query(self, mock_get):

        with open(os.path.join(RESOURCES, 'harvester_resp.json')) as json_file:
            articles = json.load(json_file)

        articles["request"]["queryString"] = 'ISSN:"1234-5678" OPEN_ACCESS:"y" UPDATE_DATE:' + self.today + ' sort_date:"y"',

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

    @patch('portality.tasks.harvester_helpers.epmc.client.EuropePMC.query')
    def test_start_multiple(self, mock_query):
        # Create a job that appears to be in progress
        job = HarvesterBackgroundTask.prepare("testuser")
        job.start()
        job.save(blocking=True)

        job2 = HarvesterBackgroundTask.prepare("testuser")
        task = HarvesterBackgroundTask(job2)
        BackgroundApi.execute(task)

        assert not mock_query.called, "mock_query was called when it shouldn't have been"

        time.sleep(2)

        job3 = models.BackgroundJob.pull(job2.id)
        assert job3.status == "error", "expected 'error', got '{x}'".format(x=job3.status)

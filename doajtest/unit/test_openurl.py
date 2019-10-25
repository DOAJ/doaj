import time

from flask import url_for

from doajtest.fixtures import JournalFixtureFactory
from doajtest.helpers import DoajTestCase
from portality import app, models


class TestOpenURL(DoajTestCase):
    @classmethod
    def setUpClass(cls):
        app.testing = True

    def setUp(self):
        super(TestOpenURL, self).setUp()

    def test_01_openurl_no_atrrs(self):
        """ Check we get the correct response from the OAI endpoint ListMetdataFormats request"""
        with self.app_test.test_request_context():
            with self.app_test.test_client() as t_client:
                resp = t_client.get(url_for('openurl.openurl'))
                assert resp.status_code == 404

                resp = t_client.get(url_for('openurl.help'))
                assert resp.status_code == 200

    def test_02_openurl_journal(self):
        journal_sources = JournalFixtureFactory.make_many_journal_sources(4, in_doaj=True)
        j_public1 = models.Journal(**journal_sources[0])
        j_public1.save(blocking=True)

        j_public2 = models.Journal(**journal_sources[1])
        j_public2.save(blocking=True)


        j_private1 = models.Journal(**journal_sources[2])
        j_private1.set_in_doaj(False)
        j_private1.save(blocking=True)

        j_private2 = models.Journal(**journal_sources[3])
        j_private2.set_in_doaj(False)
        j_private2.save(blocking=True)

        time.sleep(1)

        """ Check if we receive only journals in DOAJ """

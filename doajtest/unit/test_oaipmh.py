from portality.view import oaipmh
from portality.models import OAIPMHJournal, OAIPMHArticle
from doajtest.helpers import DoajTestCase
from doajtest.fixtures import JournalFixtureFactory
from portality import models
from portality.app import app
from lxml import etree


class TestClient(DoajTestCase):
    @classmethod
    def setUpClass(cls):
        app.testing = True

    def setUp(self):
        super(TestClient, self).setUp()

        # We're going to need this a lot.
        self.oai_ns = {'o': 'http://www.openarchives.org/OAI/2.0/'}

    def test_01_oai_ListMetadataFormats(self):
        """ Check we get the correct response from the OAI endpoint ListMetdataFormats request"""
        with app.test_client() as t_client:
            resp = t_client.get('/oai?verb=ListMetadataFormats')
            assert resp.status_code == 200

            t = etree.fromstring(resp.data)
            assert t.xpath('/o:OAI-PMH/o:ListMetadataFormats/o:metadataFormat/o:metadataPrefix', namespaces=self.oai_ns)[0].text == 'oai_dc'

    def test_02_oai_journals(self):
        """test if the OAI-PMH journal feed returns records and only displays journals accepted in DOAJ"""
        journal_sources = JournalFixtureFactory.make_many_journal_sources(2, in_doaj=True)
        j_public = models.Journal(**journal_sources[0])
        j_public.save(blocking=True)

        j_private = models.Journal(**journal_sources[1])
        j_private.set_in_doaj(False)
        j_private.save(blocking=True)

        with app.test_client() as t_client:
            resp = t_client.get('/oai?verb=ListRecords&metadataPrefix=oai_dc')
            assert resp.status_code == 200

            t = etree.fromstring(resp.data)
            print etree.tostring(t, pretty_print=True)


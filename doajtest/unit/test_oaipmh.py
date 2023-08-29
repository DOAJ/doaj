from doajtest.helpers import DoajTestCase
from doajtest.fixtures import JournalFixtureFactory
from doajtest.fixtures import ArticleFixtureFactory
from portality import models
from portality.app import app
from lxml import etree
from datetime import timedelta
from freezegun import freeze_time
from flask import url_for
import time

from portality.lib import dates
from portality.lib.dates import FMT_DATE_STD


class TestClient(DoajTestCase):
    @classmethod
    def setUpClass(cls):
        app.testing = True
        super(TestClient, cls).setUpClass()

    def setUp(self):
        super(TestClient, self).setUp()

        # We're going to need this a lot.
        self.oai_ns = {'oai': 'http://www.openarchives.org/OAI/2.0/',
                       'oai_dc': 'http://www.openarchives.org/OAI/2.0/oai_dc/',
                       'dc': 'http://purl.org/dc/elements/1.1/',
                       'xsi' : 'http://www.w3.org/2001/XMLSchema-instance'}

    def test_01_oai_ListMetadataFormats(self):
        """ Check we get the correct response from the OAI endpoint ListMetdataFormats request"""
        with self.app_test.test_request_context():
            with self.app_test.test_client() as t_client:
                resp = t_client.get(url_for('oaipmh.oaipmh', verb='ListMetadataFormats'))
                assert resp.status_code == 200

                t = etree.fromstring(resp.data)
                assert t.xpath('/oai:OAI-PMH/oai:ListMetadataFormats/oai:metadataFormat/oai:metadataPrefix', namespaces=self.oai_ns)[0].text == 'oai_dc'

    def test_02_oai_journals(self):
        """test if the OAI-PMH journal feed returns records and only displays journals accepted in DOAJ"""
        journal_sources = JournalFixtureFactory.make_many_journal_sources(2, in_doaj=True)
        j_public = models.Journal(**journal_sources[0])
        j_public.save(blocking=True)
        public_id = j_public.id

        j_private = models.Journal(**journal_sources[1])
        j_private.set_in_doaj(False)
        j_private.save(blocking=True)

        with self.app_test.test_request_context():
            with self.app_test.test_client() as t_client:
                resp = t_client.get(url_for('oaipmh.oaipmh', verb='ListRecords', metadataPrefix='oai_dc'))
                assert resp.status_code == 200

                t = etree.fromstring(resp.data)
                records = t.xpath('/oai:OAI-PMH/oai:ListRecords', namespaces=self.oai_ns)

                # Check we only have one journal returned
                assert len(records[0].xpath('//oai:record', namespaces=self.oai_ns)) == 1

                # Check we have the correct journal
                assert records[0].xpath('//dc:title', namespaces=self.oai_ns)[0].text == j_public.bibjson().title

                resp = t_client.get(url_for('oaipmh.oaipmh', verb='GetRecord', metadataPrefix='oai_dc') + '&identifier={0}'.format(public_id))
                assert resp.status_code == 200

                t = etree.fromstring(resp.data)
                records = t.xpath('/oai:OAI-PMH/oai:GetRecord', namespaces=self.oai_ns)

                # Check we only have one journal returned
                assert len(records[0].xpath('//oai:record', namespaces=self.oai_ns)) == 1

                # Check we have the correct journal
                assert records[0].xpath('//dc:title', namespaces=self.oai_ns)[0].text == j_public.bibjson().title

    def test_03_oai_resumption_token(self):
        """ Test the behaviour of the ResumptionToken in the OAI interface"""

        # Set the OAI interface to only return two identifiers at a time
        app.config['OAIPMH_LIST_IDENTIFIERS_PAGE_SIZE'] = 2

        [j0, j1, j2, j3, j4] = JournalFixtureFactory.make_many_journal_sources(5, in_doaj=True)

        # Save a single journal in the index
        jm0 = models.Journal(**j0)
        jm0.save(blocking=True)

        # ListIdentifiers - we expect no resumptionToken because all results are returned
        with self.app_test.test_request_context():
            with self.app_test.test_client() as t_client:
                resp = t_client.get(url_for('oaipmh.oaipmh', verb='ListIdentifiers', metadataPrefix='oai_dc'))
                t = etree.fromstring(resp.data)
                assert t.xpath('//oai:identifier', namespaces=self.oai_ns)[0].text == 'oai:doaj.org/journal:journalid0'
                assert t.xpath('//oai:resumptionToken', namespaces=self.oai_ns) == []

        # Populate index with 4 more journals
        for j in [j1, j2, j3, j4]:
            jm = models.Journal(**j)
            jm.save(blocking=True)

        # ListIdentifiers - we expect 5 total results and a resumptionToken to fetch the rest
        with self.app_test.test_request_context():
            with self.app_test.test_client() as t_client:
                resp = t_client.get(url_for('oaipmh.oaipmh', verb='ListIdentifiers', metadataPrefix='oai_dc'))
                t = etree.fromstring(resp.data)
                #print etree.tostring(t, pretty_print=True)
                rt = t.xpath('//oai:resumptionToken', namespaces=self.oai_ns)[0]
                assert rt.get('completeListSize') == '5'
                assert rt.get('cursor') == '2'

                # Get the next result
                resp2 = t_client.get(url_for('oaipmh.oaipmh', verb='ListIdentifiers', resumptionToken=rt.text))
                t = etree.fromstring(resp2.data)
                #print etree.tostring(t, pretty_print=True)
                rt2 = t.xpath('//oai:resumptionToken', namespaces=self.oai_ns)[0]
                assert rt2.get('completeListSize') == '5'
                assert rt2.get('cursor') == '4'

                # And the final result - check we get an empty resumptionToken
                resp3 = t_client.get(url_for('oaipmh.oaipmh', verb='ListIdentifiers', resumptionToken=rt2.text))
                t = etree.fromstring(resp3.data)
                #print etree.tostring(t, pretty_print=True)
                rt3 = t.xpath('//oai:resumptionToken', namespaces=self.oai_ns)[0]
                assert rt3.get('completeListSize') == '5'
                assert rt3.get('cursor') == '5'
                assert rt3.text is None

                # We should get an error if we request again with an empty resumptionToken
                resp4 = t_client.get(url_for('oaipmh.oaipmh', verb='ListIdentifiers') + '&resumptionToken={0}'.format(rt3.text))
                assert resp4.status_code == 200                                   # fixme: should this be a real error code?
                t = etree.fromstring(resp4.data)
                #print etree.tostring(t, pretty_print=True)

                err = t.xpath('//oai:error', namespaces=self.oai_ns)[0]
                assert 'the resumptionToken argument is invalid or expired' in err.text

    def test_04_oai_changing_index(self):
        """ Check that changes to the index don't appear in in-progress requests """

        # Set the OAI interface to only return two identifiers at a time
        app.config['OAIPMH_LIST_IDENTIFIERS_PAGE_SIZE'] = 2

        journals = JournalFixtureFactory.make_many_journal_sources(4, in_doaj=True)

        # Save our journals to the index
        for j in journals[:3]:
            jm = models.Journal(**j)
            jm.save(blocking=True)

        # ListRecords - we expect 3 total results and a resumptionToken to fetch the rest
        yesterday = (dates.now() - timedelta(days=1)).strftime(FMT_DATE_STD)
        with self.app_test.test_request_context():
            with self.app_test.test_client() as t_client:
                resp = t_client.get(url_for('oaipmh.oaipmh', verb='ListRecords', metadataPrefix='oai_dc') + '&from={0}'.format(yesterday))
                t = etree.fromstring(resp.data)
                #print etree.tostring(t, pretty_print=True)
                rt = t.xpath('//oai:resumptionToken', namespaces=self.oai_ns)[0]
                assert rt.get('completeListSize') == '3'
                assert rt.get('cursor') == '2'

                # Save another journal to the index
                [j] = journals[3:]
                jm = models.Journal(**j)
                jm.save(blocking=True)

                # Get the next result - the new journal shouldn't be added to the results
                resp2 = t_client.get('/oai?verb=ListRecords&resumptionToken={0}'.format(rt.text))
                resp2 = t_client.get(url_for('oaipmh.oaipmh', verb='ListRecords', resumptionToken=rt.text))
                t = etree.fromstring(resp2.data)
                #print etree.tostring(t, pretty_print=True)
                rt2 = t.xpath('//oai:resumptionToken', namespaces=self.oai_ns)[0]
                assert rt2.get('completeListSize') == '3'
                assert rt2.get('cursor') == '3'

                # Start a new request - we should see the new journal
                resp3 = t_client.get(url_for('oaipmh.oaipmh', verb='ListRecords', metadataPrefix='oai_dc') + '&from={0}'.format(yesterday))
                t = etree.fromstring(resp3.data)
                #print etree.tostring(t, pretty_print=True)
                rt = t.xpath('//oai:resumptionToken', namespaces=self.oai_ns)[0]
                assert rt.get('completeListSize') == '4'

    def test_05_date_ranges(self):
        """ Check that the interface adheres to the dates that records were added """

        # Set the OAI interface to only return one identifier at a time
        app.config['OAIPMH_LIST_IDENTIFIERS_PAGE_SIZE'] = 1

        journals = JournalFixtureFactory.make_many_journal_sources(4, in_doaj=True)

        now = dates.now()
        yesterday = dates.now() - timedelta(days=1)
        day_before_yesterday = dates.now() - timedelta(days=2)
        two_days_before_yesterday = dates.now() - timedelta(days=3)

        # Save half of our journals 2 days ago
        with freeze_time(day_before_yesterday):
            for j in journals[:2]:
                jm = models.Journal(**j)
                jm.save(blocking=True)

        # Save the other half of our journals today
        with freeze_time(now):
            for j in journals[2:]:
                jm = models.Journal(**j)
                jm.save(blocking=True)

        with self.app_test.test_request_context():
            with self.app_test.test_client() as t_client:
                # Request OAI journals since yesterday (looking for today's results only)
                resp = t_client.get(url_for('oaipmh.oaipmh', verb='ListRecords', metadataPrefix='oai_dc') + '&from={0}'.format(yesterday.strftime(FMT_DATE_STD)))
                t = etree.fromstring(resp.data)
                #print etree.tostring(t, pretty_print=True)
                rt = t.xpath('//oai:resumptionToken', namespaces=self.oai_ns)[0]
                assert rt.get('completeListSize') == '2'
                assert rt.get('cursor') == '1'

                for title in t.xpath('//dc:title', namespaces=self.oai_ns):
                    assert title.text in [journals[2]['bibjson']['title'], journals[3]['bibjson']['title']]

                # Request OAI journals from 3 days ago to yesterday (expecting the 2 days ago results)
                resp = t_client.get(url_for('oaipmh.oaipmh', verb='ListRecords', metadataPrefix='oai_dc') + '&from={0}&until={1}'.format(
                    two_days_before_yesterday.strftime(FMT_DATE_STD), yesterday.strftime(FMT_DATE_STD)))
                t = etree.fromstring(resp.data)
                #print etree.tostring(t, pretty_print=True)
                rt = t.xpath('//oai:resumptionToken', namespaces=self.oai_ns)[0]
                assert rt.get('completeListSize') == '2'
                assert rt.get('cursor') == '1'

                for title in t.xpath('//dc:title', namespaces=self.oai_ns):
                    assert title.text in [journals[0]['bibjson']['title'], journals[1]['bibjson']['title']]

    def test_06_identify(self):

        journal_source = JournalFixtureFactory.make_journal_source(in_doaj=True)
        j = models.Journal(**journal_source)
        j.save(blocking=True)

        with self.app_test.test_request_context():
            with self.app_test.test_client() as t_client:
                resp = t_client.get(url_for('oaipmh.oaipmh', verb='Identify', metadataPrefix='oai_dc'))
                assert resp.status_code == 200
                t = etree.fromstring(resp.data)
                records = t.xpath('/oai:OAI-PMH/oai:Identify', namespaces=self.oai_ns)
            assert len(records) == 1
            assert records[0].xpath('//oai:repositoryName', namespaces=self.oai_ns)[0].text == 'Directory of Open Access Journals'
            assert records[0].xpath('//oai:adminEmail', namespaces=self.oai_ns)[0].text == 'sysadmin@cottagelabs.com'
            assert records[0].xpath('//oai:granularity', namespaces=self.oai_ns)[0].text == 'YYYY-MM-DDThh:mm:ssZ'

    def test_07_bad_verb(self):
        journal_source = JournalFixtureFactory.make_journal_source(in_doaj=True)
        j = models.Journal(**journal_source)
        j.save(blocking=True)

        with self.app_test.test_request_context():
            with self.app_test.test_client() as t_client:
                # no verb
                resp = t_client.get(url_for('oaipmh.oaipmh', metadataPrefix='oai_dc'))
                assert resp.status_code == 200
                t = etree.fromstring(resp.data)
                records = t.xpath('/oai:OAI-PMH', namespaces=self.oai_ns)
                assert records[0].xpath('//oai:error', namespaces=self.oai_ns)[0].text == 'Value of the verb argument is not a legal OAI-PMH verb, the verb argument is missing, or the verb argument is repeated.'
                assert records[0].xpath('//oai:error', namespaces=self.oai_ns)[0].get("code") == 'badVerb'

                #invalid verb
                resp = t_client.get(url_for('oaipmh.oaipmh', verb='InvalidVerb', metadataPrefix='oai_dc'))
                assert resp.status_code == 200
                t = etree.fromstring(resp.data)
                records = t.xpath('/oai:OAI-PMH', namespaces=self.oai_ns)
                assert records[0].xpath('//oai:error', namespaces=self.oai_ns)[0].text == 'Value of the verb argument is not a legal OAI-PMH verb, the verb argument is missing, or the verb argument is repeated.'
                assert records[0].xpath('//oai:error', namespaces=self.oai_ns)[0].get("code") == 'badVerb'

    def test_08_list_sets(self):
        journal_source = JournalFixtureFactory.make_journal_source(in_doaj=True)
        j = models.Journal(**journal_source)
        j.save(blocking=True)

        with self.app_test.test_request_context():
            with self.app_test.test_client() as t_client:
                resp = t_client.get(url_for('oaipmh.oaipmh', verb='ListSets', metadataPrefix='oai_dc'))
                assert resp.status_code == 200
                t = etree.fromstring(resp.data)
                records = t.xpath('/oai:OAI-PMH/oai:ListSets', namespaces=self.oai_ns)
                sets = records[0].getchildren()
            assert len(sets) == 3
            set0 = sets[0].getchildren()
            set1 = sets[1].getchildren()
            set2 = sets[2].getchildren()
            assert set0[1].text == 'LCC:Economic theory. Demography'
            assert set1[1].text == 'LCC:Social Sciences'
            assert set2[1].text == 'LCC:Veterinary medicine'

            # check that we can retrieve a record with one of those sets
            with self.app_test.test_client() as t_client:
                resp = t_client.get(url_for('oaipmh.oaipmh', verb='ListRecords', metadataPrefix='oai_dc', set=set0[0].text))
                assert resp.status_code == 200
                t = etree.fromstring(resp.data)
                records = t.xpath('/oai:OAI-PMH/oai:ListRecords', namespaces=self.oai_ns)
                results = records[0].getchildren()
            assert len(results) == 1


    def test_09_article(self):
        """test if the OAI-PMH journal feed returns records and only displays journals accepted in DOAJ"""
        article_source = ArticleFixtureFactory.make_article_source(eissn='1234-1234', pissn='5678-5678,', in_doaj=False)
        """test if the OAI-PMH article feed returns records and only displays articles accepted in DOAJ"""
        a_private = models.Article(**article_source)
        ba = a_private.bibjson()
        ba.title = "Private Article"
        a_private.save(blocking=True)

        article_source = ArticleFixtureFactory.make_article_source(eissn='4321-4321', pissn='8765-8765,', in_doaj=True)
        a_public = models.Article(**article_source)
        ba = a_public.bibjson()
        ba.title = "Public Article"
        a_public.save(blocking=True)
        public_id = a_public.id

        time.sleep(1)

        with self.app_test.test_request_context():
            with self.app_test.test_client() as t_client:
                resp = t_client.get(url_for('oaipmh.oaipmh',  specified='article', verb='ListRecords', metadataPrefix='oai_dc'))
                assert resp.status_code == 200

                t = etree.fromstring(resp.data)
                records = t.xpath('/oai:OAI-PMH/oai:ListRecords', namespaces=self.oai_ns)

                # Check we only have one journal returned
                r = records[0].xpath('//oai:record', namespaces=self.oai_ns)
                assert len(r) == 1

                # Check we have the correct journal
                title = r[0].xpath('//dc:title', namespaces=self.oai_ns)[0].text
                # check orcid_id xwalk
                assert str(records[0].xpath('//dc:creator/@id', namespaces=self.oai_ns)[0]) == a_public.bibjson().author[0].get("orcid_id")
                assert records[0].xpath('//dc:title', namespaces=self.oai_ns)[0].text == a_public.bibjson().title

                resp = t_client.get(url_for('oaipmh.oaipmh',  specified='article', verb='GetRecord', metadataPrefix='oai_dc') + '&identifier=abcdefghijk_article')
                assert resp.status_code == 200

                t = etree.fromstring(resp.data)
                records = t.xpath('/oai:OAI-PMH/oai:GetRecord', namespaces=self.oai_ns)

                # Check we only have one journal returnedt
                kids = records[0].getchildren()
                r = records[0].xpath('//oai:record', namespaces=self.oai_ns)
                assert len(r) == 1

                # Check we have the correct journal
                assert records[0].xpath('//dc:title', namespaces=self.oai_ns)[0].text == a_public.bibjson().title

    def test_10_subjects(self):
        """test if the OAI-PMH journal feed returns correct journals when set specified"""
        journal_source = JournalFixtureFactory.make_journal_source(in_doaj=True)
        j_public = models.Journal(**journal_source)
        j_public.save(blocking=True)
        public_id = j_public.id

        with self.app_test.test_request_context():
            # Check whether the journal is found for its specific set: Veterinary Medicine (TENDOlZldGVyaW5hcnkgbWVkaWNpbmU)
            with self.app_test.test_client() as t_client:
                resp = t_client.get(url_for('oaipmh.oaipmh', verb='ListRecords', metadataPrefix='oai_dc', set='TENDOlZldGVyaW5hcnkgbWVkaWNpbmU~'))
                assert resp.status_code == 200

                t = etree.fromstring(resp.data)
                records = t.xpath('/oai:OAI-PMH/oai:ListRecords', namespaces=self.oai_ns)

                # Check we only have one journal returned
                assert len(records[0].xpath('//oai:record', namespaces=self.oai_ns)) == 1

                # Check we have the correct journal
                assert records[0].xpath('//dc:title', namespaces=self.oai_ns)[0].text == j_public.bibjson().title

                #check we have expected subjects (Veterinary Medicine but not Agriculture)
                subjects = records[0].xpath('//dc:subject', namespaces=self.oai_ns)
                assert len(subjects) != 0

                subjects_txt = list(map(lambda s: s.text, subjects))
                assert "Veterinary medicine" in subjects_txt
                assert not "Agriculture" in subjects_txt

        # check we can still find the record in Agriculture set (parent of Veterinary Medicine)
        with self.app_test.test_request_context():
            # Check whether the journal is found for more general set: Agriculture (TENDOkFncmljdWx0dXJl)
            with self.app_test.test_client() as t_client:
                resp = t_client.get(url_for('oaipmh.oaipmh', verb='ListRecords', metadataPrefix='oai_dc', set='TENDOkFncmljdWx0dXJl~'))
                assert resp.status_code == 200

                t = etree.fromstring(resp.data)
                records = t.xpath('/oai:OAI-PMH/oai:ListRecords', namespaces=self.oai_ns)

                sets = records[0].getchildren()

                assert len(sets) == 1
                set0 = sets[0].getchildren()

                # Check we only have one journal returned
                assert len(records[0].xpath('//oai:record', namespaces=self.oai_ns)) == 1

                # Check we have the correct journal
                assert records[0].xpath('//dc:title', namespaces=self.oai_ns)[0].text == j_public.bibjson().title


    def test_11_oai_dc_attr(self):
        """test if the OAI-PMH article feed returns record with correct attributes in oai_dc element"""
        article_source = ArticleFixtureFactory.make_article_source(eissn='1234-1234', pissn='5678-5678,', in_doaj=True)
        a_private = models.Article(**article_source)
        ba = a_private.bibjson()
        ba.title = "Private Article"
        a_private.save(blocking=True)

        time.sleep(1)

        with self.app_test.test_request_context():
            with self.app_test.test_client() as t_client:
                resp = t_client.get(url_for('oaipmh.oaipmh',  specified='article', verb='ListRecords', metadataPrefix='oai_dc'))
                assert resp.status_code == 200

                t = etree.fromstring(resp.data)
                # find metadata element of our record
                elem = t.xpath('/oai:OAI-PMH/oai:ListRecords/oai:record/oai:metadata', namespaces=self.oai_ns)
                # metadata element should have only one child, "dc" with correct nsmap
                oai_dc = elem[0].getchildren()
                assert len(oai_dc) == 1
                assert oai_dc[0].tag == "{%s}" % self.oai_ns["oai_dc"] + "dc"
                assert oai_dc[0].nsmap["xsi"] == self.oai_ns["xsi"]

        journal_sources = JournalFixtureFactory.make_many_journal_sources(2, in_doaj=True)
        j_public = models.Journal(**journal_sources[0])
        j_public.save(blocking=True)
        public_id = j_public.id

        with self.app_test.test_request_context():
            with self.app_test.test_client() as t_client:
                resp = t_client.get(
                    url_for('oaipmh.oaipmh', specified='article', verb='ListRecords', metadataPrefix='oai_dc'))
                assert resp.status_code == 200

                t = etree.fromstring(resp.data)
                # find metadata element of our record
                elem = t.xpath('/oai:OAI-PMH/oai:ListRecords/oai:record/oai:metadata', namespaces=self.oai_ns)
                #metadata element should have only one child, "dc" with correct nsmap
                oai_dc = elem[0].getchildren()
                assert len(oai_dc) == 1
                assert oai_dc[0].tag == "{%s}" % self.oai_ns["oai_dc"] + "dc"
                assert oai_dc[0].nsmap["xsi"] == self.oai_ns["xsi"]

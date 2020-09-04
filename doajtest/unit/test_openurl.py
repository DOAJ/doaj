from flask import url_for

from doajtest.fixtures import JournalFixtureFactory
from doajtest.helpers import DoajTestCase
from portality import app, models
from urllib.parse import urlparse

QUERY='url_ver=Z39.88-2004&url_ctx_fmt=info%3Aofi%2Ffmt%3Akev%3Amtx%3Actx&rft_val_fmt=info%3Aofi%2Ffmt%3Akev%3Amtx%3Ajournal'


class TestOpenURL(DoajTestCase):
    @classmethod
    def setUpClass(cls):
        app.testing = True

    def setUp(self):
        super(TestOpenURL, self).setUp()

    def test_01_openurl_no_atrrs(self):
        """ Check we get the correct response from the OpenURL endpoints"""
        with self.app_test.test_request_context():
            with self.app_test.test_client() as t_client:
                # No object requested - not found
                resp = t_client.get(url_for('openurl.openurl'))
                assert resp.status_code == 404

                # Help requested - help page is displayed
                resp = t_client.get(url_for('openurl.help'))
                assert resp.status_code == 200
                assert resp.mimetype == 'text/html'

    def test_02_openurl_journal_retrieve(self):
        """ Check journal retrieval via OpenURL """
        [j_public_source, j_private_source] = JournalFixtureFactory.make_many_journal_sources(2, in_doaj=True)
        j_public1 = models.Journal(**j_public_source)
        j_public1.set_in_doaj(True)
        j_public1.save(blocking=True)

        j_private1 = models.Journal(**j_private_source)
        j_private1.set_in_doaj(False)
        j_private1.save(blocking=True)

        def compare_queries(q1, q2):
            q1bits = q1.split("&")
            q2bits = q2.split("&")
            q1bits.sort()
            q2bits.sort()
            return q1bits == q2bits

        # Check we receive only journals in DOAJ
        with self.app_test.test_request_context():
            with self.app_test.test_client() as t_client:
                # Make an OpenURL 0.1 request, it should be redirected into an OpenURL 1.0 request.
                resp = t_client.get(url_for('openurl.openurl', issn=j_public1.bibjson().get_one_identifier('pissn')))
                assert resp.status_code == 301

                # Check the redirect is of the format we expect and that the in_doaj  journal is accessible
                query = urlparse(resp.location).query
                assert compare_queries(query, QUERY + '&rft.issn=' + j_public1.bibjson().get_one_identifier('pissn'))
                resp = t_client.get(resp.location)
                assert resp.status_code == 302

                # The same redirect should happen for a journal that's not public, but it should return a 404.
                resp = t_client.get(url_for('openurl.openurl', issn=j_private1.bibjson().get_one_identifier('pissn')))
                assert resp.status_code == 301
                query = urlparse(resp.location).query
                assert compare_queries(query, QUERY + '&rft.issn=' + j_private1.bibjson().get_one_identifier('pissn'))
                resp = t_client.get(resp.location)
                assert resp.status_code == 404

                # Check a request in the correct format isn't redirected
                resp = t_client.get(url_for('openurl.openurl',
                                            url_ver='Z39.88-2004',
                                            url_ctx_fmt='info:ofi/fmt:kev:mtx:ctx',
                                            ft_val_fmt='info:ofi/fmt:kev:mtx:journal',
                                            issn=j_public1.bibjson().get_one_identifier('pissn')))
                assert resp.status_code == 302

    def test_03_openurl_article_retrieve(self):
        pass
        # TODO

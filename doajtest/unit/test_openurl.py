import time
from flask import url_for

from doajtest.fixtures import JournalFixtureFactory, ArticleFixtureFactory
from doajtest.helpers import DoajTestCase
from portality import app, models
from urllib.parse import urlparse

QUERY = 'url_ver=Z39.88-2004' \
      '&url_ctx_fmt=info%3Aofi%2Ffmt%3Akev%3Amtx%3Actx' \
      '&rft_val_fmt=info%3Aofi%2Ffmt%3Akev%3Amtx%3Ajournal'


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

                # Check the redirect is of the format we expect and that the in_doaj journal is accessible
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

    def test_03_openurl_multiple_prarameters(self):
        """ Check journal retrieval via multiple OpenURL parameters """
        [j_matching_source, j_nonmatching_source] = JournalFixtureFactory.make_many_journal_sources(2, in_doaj=True)
        j_matching = models.Journal(**j_matching_source)
        j_matching.set_in_doaj(True)
        j_matching.save(blocking=True)

        param_eissn = j_matching.bibjson().first_eissn
        param_pissn = j_matching.bibjson().first_pissn
        param_title = j_matching.bibjson().title

        j_nonmatching = models.Journal(**j_nonmatching_source)
        j_nonmatching.set_in_doaj(True)
        param_different_title = "A new title not the same as the old title"
        j_nonmatching.bibjson().title = param_different_title
        j_nonmatching.bibjson().eissn = param_eissn
        j_nonmatching.bibjson().pissn = param_pissn
        j_nonmatching.save(blocking=True)

        with self.app_test.test_request_context():
            with self.app_test.test_client() as t_client:

                # A query with 3 criteria + genre journal
                resp = t_client.get(url_for('openurl.openurl',
                                            url_ver='Z39.88-2004',
                                            url_ctx_fmt='info:ofi/fmt:kev:mtx:ctx',
                                            ft_val_fmt='info:ofi/fmt:kev:mtx:journal',
                                            pissn=param_pissn,
                                            eissn=param_eissn,
                                            jtitle=param_title,
                                            genre='journal'))

                assert resp.status_code == 302
                assert resp.location == url_for('doaj.toc', identifier=j_matching.id, _external=True)

                # A query without genre to show it's the default
                resp = t_client.get(url_for('openurl.openurl',
                                            url_ver='Z39.88-2004',
                                            url_ctx_fmt='info:ofi/fmt:kev:mtx:ctx',
                                            ft_val_fmt='info:ofi/fmt:kev:mtx:journal',
                                            pissn=param_pissn,
                                            eissn=param_eissn,
                                            jtitle=param_title))

                assert resp.status_code == 302
                assert resp.location == url_for('doaj.toc', identifier=j_matching.id, _external=True)

                # Search for the second journal by its differing title
                resp = t_client.get(url_for('openurl.openurl',
                                            url_ver='Z39.88-2004',
                                            url_ctx_fmt='info:ofi/fmt:kev:mtx:ctx',
                                            ft_val_fmt='info:ofi/fmt:kev:mtx:journal',
                                            issn=param_pissn,
                                            eissn=param_eissn,
                                            jtitle=param_different_title,
                                            genre='journal'))

                assert resp.status_code == 302
                assert resp.location == url_for('doaj.toc', identifier=j_nonmatching.id, _external=True)

                # Relaxing title constraint means both journals match, but we're served the 'best match' according to ES
                resp = t_client.get(url_for('openurl.openurl',
                                            url_ver='Z39.88-2004',
                                            url_ctx_fmt='info:ofi/fmt:kev:mtx:ctx',
                                            ft_val_fmt='info:ofi/fmt:kev:mtx:journal',
                                            issn=param_pissn,
                                            eissn=param_eissn))

                assert resp.status_code == 302

    def test_04_openurl_article_retrieve(self):
        """ Check we can retrieve articles from OpenURL """
        [j_indoaj_source, j_notindoaj_source] = JournalFixtureFactory.make_many_journal_sources(2, in_doaj=True)
        j_indoaj = models.Journal(**j_indoaj_source)
        j_indoaj.save(blocking=True)

        j_indoaj_arts = ArticleFixtureFactory.make_many_article_sources(2, in_doaj=True,
                                                                                  pissn=j_indoaj.bibjson().first_pissn,
                                                                                  eissn=j_indoaj.bibjson().first_eissn)
        [models.Article(**m).save(blocking=True) for m in j_indoaj_arts]

        j_notindoaj = models.Journal(**j_notindoaj_source)
        j_notindoaj.set_in_doaj(False)
        j_notindoaj.save(blocking=True)

        notindoaj_arts = ArticleFixtureFactory.make_many_article_sources(2, in_doaj=False,
                                                                                  pissn=j_notindoaj.bibjson().first_pissn,
                                                                                  eissn=j_notindoaj.bibjson().first_eissn)
        [models.Article(**m).save(blocking=True) for m in notindoaj_arts]

        # Check we can get an in_doaj article from an openURL request
        with self.app_test.test_request_context():
            with self.app_test.test_client() as t_client:
                # Make an OpenURL 0.1 request, it should be redirected into an OpenURL 1.0 request.
                resp = t_client.get(url_for('openurl.openurl', genre='article', aulast='The Author'))
                assert resp.status_code == 301

                # Check the redirect works and the in_doaj article is accessible
                resp = t_client.get(resp.location)
                assert resp.status_code == 302
                retrieved_article_id = resp.location.split('/').pop()
                art = models.Article.pull(retrieved_article_id)
                assert art.is_in_doaj() is True

                # Check we can't retrieve an article that's not in_doaj (but the redirect occurs)
                title = notindoaj_arts.pop()['bibjson']['title']
                resp = t_client.get(url_for('openurl.openurl', genre='article', atitle=title))
                assert resp.status_code == 301
                resp = t_client.get(resp.location)
                assert resp.status_code == 404

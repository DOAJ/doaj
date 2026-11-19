from flask import url_for

from doajtest.fixtures import JournalFixtureFactory, ArticleFixtureFactory
from doajtest.helpers import DoajTestCase
from portality import app, models
from portality.models.openurl import OpenURLRequest, UnsupportedOpenURLQuery
from urllib.parse import urlparse

QUERY = ('url_ver=Z39.88-2004'
         '&url_ctx_fmt=info:ofi/fmt:kev:mtx:ctx'
         '&rft_val_fmt=info:ofi/fmt:kev:mtx:journal')


class TestOpenURL(DoajTestCase):
    @classmethod
    def setUpClass(cls):
        app.testing = True
        super(TestOpenURL, cls).setUpClass()

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

        art_source = ArticleFixtureFactory.make_article_source(eissn=param_eissn, pissn=param_pissn)
        art_source["bibjson"]["journal"]["volume"] = "1"
        art = models.Article(**art_source)
        art.save(blocking=True)

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
                                            genre='journal',
                                            volume="1"))

                assert resp.status_code == 302

                # FIXME: we have removed volumes from the ToC so we can't resolve the volume in the query
                # assert resp.location == url_for('doaj.toc', identifier=j_matching.id, volume="1")
                assert resp.location == url_for('doaj.toc', identifier=j_matching.id)

                # A query without genre to show it's the default
                resp = t_client.get(url_for('openurl.openurl',
                                            url_ver='Z39.88-2004',
                                            url_ctx_fmt='info:ofi/fmt:kev:mtx:ctx',
                                            ft_val_fmt='info:ofi/fmt:kev:mtx:journal',
                                            pissn=param_pissn,
                                            eissn=param_eissn,
                                            jtitle=param_title))

                assert resp.status_code == 302
                assert resp.location == url_for('doaj.toc', identifier=j_matching.id)

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
                assert resp.location == url_for('doaj.toc', identifier=j_nonmatching.id)

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

    def test_05_query_es_unsupported_field_raises(self):
        """ query_es() raises UnsupportedOpenURLQuery when every field supplied is unmapped (issue #4257/#4124) """
        # 'au' is a real OpenURL schema field (and a real property on OpenURLRequest),
        # but DOAJ has no ES mapping for it - this is the exact scenario from #4257
        req = OpenURLRequest(au="Smith, John", genre="journal")
        with self.assertRaises(UnsupportedOpenURLQuery):
            req.query_es()

    def test_06_query_es_unsupported_genre_raises(self):
        """ query_es() raises UnsupportedOpenURLQuery for a genre DOAJ doesn't recognise """
        # 'conference' is a real OpenURL genre (see OpenURLRequest.genre docstring),
        # DOAJ just doesn't support searching against it
        req = OpenURLRequest(jtitle="Nature", genre="conference")
        with self.assertRaises(UnsupportedOpenURLQuery):
            req.query_es()

    def test_07_query_es_mixed_supported_and_unsupported_fields(self):
        """ An unsupported field alongside a supported one is skipped, not fatal """
        req = OpenURLRequest(au="Smith, John", jtitle="Nature", genre="journal")
        # should not raise - 'au' is skipped, 'jtitle' still gets searched on
        result = req.query_es()
        self.assertIsNotNone(result)

    def test_08_query_es_no_fields_at_all_returns_none(self):
        """ A request with no OpenURL fields set at all still returns None (not an
        unconstrained/all-in_doaj query, and not an UnsupportedOpenURLQuery either -
        there was nothing wrong with the request, it just didn't ask for anything) """
        req = OpenURLRequest(genre="journal")
        result = req.query_es()
        self.assertIsNone(result)

    def test_09_openurl_view_unsupported_field_returns_400(self):
        """ End-to-end: the exact reproduction case from the ticket returns 400, not a 500 """
        with self.app_test.test_request_context():
            with self.app_test.test_client() as t_client:
                resp = t_client.get(url_for('openurl.openurl',
                                            url_ver='Z39.88-2004',
                                            url_ctx_fmt='info:ofi/fmt:kev:mtx:ctx',
                                            rft_val_fmt='info:ofi/fmt:kev:mtx:journal',
                                            au='Smith, John'))
                assert resp.status_code == 400

    def test_10_openurl_view_unsupported_genre_returns_400(self):
        """ End-to-end: an unrecognised genre also returns 400, not a 500 """
        with self.app_test.test_request_context():
            with self.app_test.test_client() as t_client:
                resp = t_client.get(url_for('openurl.openurl',
                                            url_ver='Z39.88-2004',
                                            url_ctx_fmt='info:ofi/fmt:kev:mtx:ctx',
                                            rft_val_fmt='info:ofi/fmt:kev:mtx:journal',
                                            genre='conference',
                                            jtitle='Nature'))
                assert resp.status_code == 400

    def test_11_openurl_view_mixed_fields_still_works(self):
        """ End-to-end: an unsupported field alongside a valid, matching one still
        resolves normally (the unsupported field is dropped, not fatal) """
        [j_source] = JournalFixtureFactory.make_many_journal_sources(1, in_doaj=True)
        j = models.Journal(**j_source)
        j.set_in_doaj(True)
        j.save(blocking=True)

        with self.app_test.test_request_context():
            with self.app_test.test_client() as t_client:
                resp = t_client.get(url_for('openurl.openurl',
                                            url_ver='Z39.88-2004',
                                            url_ctx_fmt='info:ofi/fmt:kev:mtx:ctx',
                                            rft_val_fmt='info:ofi/fmt:kev:mtx:journal',
                                            au='Smith, John',
                                            jtitle=j.bibjson().title,
                                            genre='journal'))
                assert resp.status_code == 302

    def test_12_openurl_view_only_meta_params_returns_404(self):
        """ A request with url_ver/url_ctx_fmt/rft_val_fmt but no actual rft.* search
        fields should 404 (nothing to search on), not silently run an unconstrained
        in_doaj query and redirect to an arbitrary result """
        with self.app_test.test_request_context():
            with self.app_test.test_client() as t_client:
                resp = t_client.get(url_for('openurl.openurl',
                                            url_ver='Z39.88-2004',
                                            url_ctx_fmt='info:ofi/fmt:kev:mtx:ctx',
                                            rft_val_fmt='info:ofi/fmt:kev:mtx:journal'))
                assert resp.status_code == 404

    def test_13_article_title_no_match_is_404_not_400(self):
        """ The jtitle->stitle fallthrough retry has no article mapping; a valid article query with no hits must stay a 404 """
        with self.app_test.test_request_context():
            with self.app_test.test_client() as t_client:
                resp = t_client.get(url_for('openurl.openurl',
                                            url_ver='Z39.88-2004',
                                            url_ctx_fmt='info:ofi/fmt:kev:mtx:ctx',
                                            rft_val_fmt='info:ofi/fmt:kev:mtx:journal',
                                            genre='article',
                                            jtitle='No Such Title XYZ'))
                assert resp.status_code == 404

    def _save_two_articles_in_one_journal(self):
        """ Two in_doaj articles sharing a journal title and volume (as the fixtures make them), but with distinct titles """
        art_sources = ArticleFixtureFactory.make_many_article_sources(2, in_doaj=True)
        arts = [models.Article(**s) for s in art_sources]
        for a in arts:
            a.save(blocking=True)
        return arts

    def _openurl(self, t_client, **params):
        return t_client.get(url_for('openurl.openurl',
                                    url_ver='Z39.88-2004',
                                    url_ctx_fmt='info:ofi/fmt:kev:mtx:ctx',
                                    rft_val_fmt='info:ofi/fmt:kev:mtx:journal',
                                    **params))

    def test_14_article_ambiguous_after_skipping_unsupported_field_is_400(self):
        """ Skipping an unsupported field (artnum) mustn't broaden an article query into a redirect to an arbitrary
        one of several matches - the skipped field might be what told them apart """
        arts = self._save_two_articles_in_one_journal()
        jtitle = arts[0].bibjson().journal_title
        with self.app_test.test_request_context():
            with self.app_test.test_client() as t_client:
                resp = self._openurl(t_client, genre='article', jtitle=jtitle, artnum='123')
                assert resp.status_code == 400, resp.status_code

                # the same query without the unsupported field is unchanged: best match by ES
                resp = self._openurl(t_client, genre='article', jtitle=jtitle)
                assert resp.status_code == 302, resp.status_code

    def test_15_article_unique_after_skipping_unsupported_field_still_resolves(self):
        """ If the supported fields alone identify exactly one article, the skipped field doesn't matter """
        arts = self._save_two_articles_in_one_journal()
        target = arts[1]
        with self.app_test.test_request_context():
            with self.app_test.test_client() as t_client:
                resp = self._openurl(t_client, genre='article', atitle=target.bibjson().title,
                                     jtitle=target.bibjson().journal_title, artnum='123', aufirst='Someone')
                assert resp.status_code == 302, resp.status_code
                assert resp.location.endswith(url_for('doaj.article_page', identifier=target.id)), resp.location

    def test_16_article_title_no_match_does_not_retry_without_title(self):
        """ For articles the jtitle->stitle retry would drop the title (stitle has no article mapping) and re-run only
        the other terms. A journal title that matches nothing must 404, not redirect to some article in that volume """
        arts = self._save_two_articles_in_one_journal()
        volume = arts[0].bibjson().volume
        with self.app_test.test_request_context():
            with self.app_test.test_client() as t_client:
                resp = self._openurl(t_client, genre='article', jtitle='No Such Journal XYZ', volume=volume)
                assert resp.status_code == 404, resp.status_code

                # sanity check: the volume alone does find articles, so the 404 above is down to the title
                resp = self._openurl(t_client, genre='article', volume=volume)
                assert resp.status_code == 302, resp.status_code

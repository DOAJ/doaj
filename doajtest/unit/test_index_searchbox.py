from doajtest.helpers import DoajTestCase
from flask import url_for


class TestSearchBox(DoajTestCase):

    def setUp(self):
        super(TestSearchBox, self).setUp()

    def tearDown(self):
        super(TestSearchBox, self).tearDown()

    def test_01_with_referrer(self):
        """ Utilise the search endpoint using the ref field. We expect a redirect with the referrer to be appended """
        with self.app_test.test_client() as c:
            resp1 = c.post('/search?source={"query": {"query_string": {"query": "cheese", "default_operator": "AND"}}}',
                           data={'ref': 'homepage-box', 'origin': 'ui'})
            assert resp1.status_code == 302, resp1.status_code
            assert resp1.location.endswith('&ref=homepage-box')

            resp2 = c.post('/search?source={"query": {"query_string": {"query": "cheese", "default_operator": "AND"}}}',
                           data={'ref': 'homepage-box', 'origin': 'ui'}, follow_redirects=True)
            assert resp2.status_code == 200, resp2.status_code

    def test_02_without_origin(self):
        """ Omit the origin field when emulating the text box - this is disallowed."""
        with self.app_test.test_client() as c:
            resp = c.post('/search?source={"query": {"query_string": {"query": "cheese", "default_operator": "AND"}}}',
                          data={'ref': 'homepage-box'})
            assert resp.status_code == 400, resp.status_code
        pass

    def test_03_without_referrer(self):
        """ Omit the referrer field when emulating the text box """
        with self.app_test.test_client() as c:
            resp = c.post('/search?source={"query": {"query_string": {"query": "cheese", "default_operator": "AND"}}}',
                          data={'origin': 'ui'})
            assert resp.status_code == 400, resp.status_code
        pass

    def test_04_legacy_search_routes(self):
        with self.app_test.test_request_context():

            with self.app_test.test_client() as t:
                # A plain /search goes to the journal search
                resp = t.get('/search')
                assert resp.status_code == 301, resp.status_code
                assert resp.location == url_for('doaj.journals_search', _external=True), resp.location

                # A legacy /search?source=...journal... also goes to the journal search page
                resp = t.get('/search?source={"query": {"filtered": {"filter": {"bool": {"must": [{"term": {"_type": "journal"}}]}}, "query": {"match_all": {}}}}}')
                assert resp.status_code == 301, resp.status_code
                assert resp.location == url_for('doaj.journals_search', _external=True), resp.location

                # A legacy /search?source=...article... goes to the article search page
                resp = t.get('/search?source={"query":{"filtered":{"filter":{"bool":{"must":[{"term":{"_type":"article"}}]}},"query":{"match_all":{}}}}}')
                assert resp.status_code == 301, resp.status_code
                assert resp.location == url_for('doaj.articles_search', _external=True), resp.location

                # Even if there's whitespace in the query
                resp = t.get('/search?source={"query": {"filtered": {"filter": {"bool": {"must": [{"term": {"_type": "article"}}]}}, "query": {"match_all": {}}}}}')
                assert resp.status_code == 301, resp.status_code
                assert resp.location == url_for('doaj.articles_search', _external=True), resp.location

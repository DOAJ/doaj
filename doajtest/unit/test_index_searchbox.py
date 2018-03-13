from doajtest.helpers import DoajTestCase


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

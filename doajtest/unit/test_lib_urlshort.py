import time

from doajtest.helpers import DoajTestCase, patch_config
from portality import models
from portality.lib import urlshort
from portality.models import UrlShortener
from portality.util import url_for
from portality.lib.thread_utils import wait_until


def wait_any_url_shortener():
    models.UrlShortener.refresh()
    return models.UrlShortener.count() > 0


class TestLibUrlshort(DoajTestCase):

    def test_create_new_alias(self):
        n_samples = 3
        aliases = {urlshort.create_new_alias() for _ in range(n_samples)}
        self.assertEqual(len(aliases), n_samples)

        assert len(aliases) == n_samples
        assert len(list(aliases)[0]) == urlshort.alias_len

    def test_parse_shortened_url(self):
        alias = 'alias_abc'
        assert alias in urlshort.parse_shortened_url(alias)

    def test_add_url_shortener(self):
        url = 'http://aabbcc.com'
        surl = urlshort.add_url_shortener(url)

        assert surl
        assert isinstance(surl, str)

        time.sleep(2)
        UrlShortener.refresh()

        surl2 = urlshort.add_url_shortener(url)
        assert surl == surl2

        surl3 = urlshort.add_url_shortener(url + 'xxxx')
        assert surl != surl3

    def test_find_shortened_url(self):
        url = 'http://aabbcc.com'
        assert urlshort.find_shortened_url(url) is None

        surl = urlshort.add_url_shortener(url)

        time.sleep(2)
        UrlShortener.refresh()

        surl2 = urlshort.find_shortened_url(url)
        assert surl == surl2

    def test_find_url_by_alias(self):
        data = {}
        for idx in range(3):
            url = f'/{idx}'
            surl = urlshort.add_url_shortener(url)
            alias = surl[surl.rfind('/') + 1:]
            data[alias] = url

        wait_until(wait_any_url_shortener)

        results = models.UrlShortener.q2obj()

        alias = results[0].alias
        assert urlshort.find_url_by_alias(alias) == data[alias]


def surl_to_alias(surl):
    alias = surl[surl.rfind('/') + 1:]
    return alias


class TestUrlshortRoute(DoajTestCase):
    def test_urlshort_route(self):
        url = 'https://www.google.com'
        surl = urlshort.add_url_shortener(url)
        wait_until(wait_any_url_shortener)

        with self.app_test.test_client() as c:
            rv = c.get(surl)
            assert rv.status_code == 302
            assert rv.headers['Location'] == url

    def test_urlshort_route__not_found(self):
        with self.app_test.test_client() as c:
            rv = c.get(urlshort.parse_shortened_url('nnnnnnnnot_found'))
            assert rv.status_code == 404

    def test_create_shorten_url(self):
        data = {'url': 'http://localhost:5004/search/journals'}
        with self.app_test.test_client() as c:
            rv = c.post(url_for('doajservices.shorten'), json=data)
            assert rv.status_code == 200
            assert rv.json['short_url']

        wait_until(wait_any_url_shortener)
        assert urlshort.find_url_by_alias(surl_to_alias(rv.json['short_url'])) == data['url']

    def test_create_shorten_url__invalid(self):
        data = {'url': 'http://localhost:5004/invalid'}
        with self.app_test.test_client() as c:
            rv = c.post(url_for('doajservices.shorten'), json=data)
            assert rv.status_code == 400

    def test_create_shorten_url__limit_reached(self):
        orig_config = patch_config(self.app_test, {'URLSHORT_LIMIT': 1})
        data = {'url': 'http://localhost:5004/search/journals'}
        with self.app_test.test_client() as c:
            rv = c.post(url_for('doajservices.shorten'), json=data)
            assert rv.status_code != 429

            wait_until(wait_any_url_shortener)

            rv = c.post(url_for('doajservices.shorten'), json=data)
            assert rv.status_code == 429

        patch_config(self.app_test, orig_config)

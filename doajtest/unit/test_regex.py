from doajtest.helpers import DoajTestCase
from portality import regex


class TestRegex(DoajTestCase):

    def test_http_url(self):
        assert regex.HTTP_URL_COMPILED.match('http://example.xx')
        assert regex.HTTP_URL_COMPILED.match('http://example.xx:999')
        assert regex.HTTP_URL_COMPILED.match('http://example.xx:999/a/b/c')
        assert regex.HTTP_URL_COMPILED.match('http://example.xx:999/a/b/c?d=e')
        assert regex.HTTP_URL_COMPILED.match('http://example.xx:999/a/b/c?d=1&f=2#qq')
        assert regex.HTTP_URL_COMPILED.match('http://example-xxxx.xx:999/a/b/c?d=1&f=2#qq')
        assert regex.HTTP_URL_COMPILED.match('http://example-xxxx.xx:80/a/b/c?d=1&f=2#qq')

        assert not regex.HTTP_URL_COMPILED.match('http://example.xx:999/a/b/a c?d e=1&f=2#qq')
        assert not regex.HTTP_URL_COMPILED.match('http://example.xx:999/a/b/c?d e=1&f=2#qq')
        assert not regex.HTTP_URL_COMPILED.match('http://example.xx:999/a/b/c?  d e=1&f=2#qq')

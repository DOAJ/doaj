from doajtest.helpers import DoajTestCase
from urllib.parse import quote_plus, urlparse


class TestCookieConsent(DoajTestCase):

    def test_01_cookie_consent_permitted_domains(self):
        """ Ensure we only redirect to our own domain via cookie consent """

        with self.app_test.test_client() as t_client:
            # Ensure only relative redirects are permitted
            empty_redirect = t_client.get('/cookie_consent')
            assert empty_redirect.status_code == 200

            permitted_redirect = t_client.get('/cookie_consent?continue=%2Farticle%2Fuuid')
            assert permitted_redirect.status_code == 302
            assert permitted_redirect.location == '/article/uuid'

            permitted_redirect_params = t_client.get('/cookie_consent?continue=' + quote_plus('/apply?errors=numerous'))
            assert permitted_redirect_params.status_code == 302
            assert permitted_redirect_params.location == '/apply?errors=numerous'

    def test_02_cookie_consent_invalid_domains(self):
        """ Any redirect to another domain is rejected via cookie consent """

        with self.app_test.test_client() as t_client:
            invalid_redirect = t_client.get(
                '/cookie_consent?continue=https%3A%2F%2Fa_nasty_phishing_site.com%2Femailform%3Fdeeds%3Devil')
            assert invalid_redirect.status_code == 400

            # The best we can do - a redirect that looks like a path should try to serve from our domain, fail with 404
            invalid_redirect_no_scheme = t_client.get(
                '/cookie_consent?continue=a_nasty_phishing_site.com%2Femailform%3Fdeeds%3Devil')
            assert invalid_redirect_no_scheme.status_code == 302
            assert not invalid_redirect_no_scheme.location.startswith('http')
            assert urlparse(invalid_redirect_no_scheme.location).path == 'a_nasty_phishing_site.com/emailform'
            assert urlparse(invalid_redirect_no_scheme.location).netloc == ''

            invalid_redirect_ip = t_client.get(
                '/cookie_consent?continue=1.2.3.4%2Femailform%3Fdeeds%3Devil')
            assert invalid_redirect_ip.status_code == 302
            assert not invalid_redirect_ip.location.startswith('http')
            assert urlparse(invalid_redirect_ip.location).path == '1.2.3.4/emailform'
            assert urlparse(invalid_redirect_ip.location).netloc == ''

from flask import session
from flask_babel import gettext
from contextlib import contextmanager
from doajtest.helpers import DoajTestCase

class TestAdminEditMetadata(DoajTestCase):

    def test_default_locale(self):
        """Test default locale is English"""
        with self.app_test.test_client() as client:
            response = client.get('/apply')
            assert gettext("Open access compliance") == "Open access compliance"
            self.assertEqual(session.get('lang'), 'en')

    def test_french_locale_selection(self):
        """Test French locale selection"""
        with self.app_test.test_client() as client:
            response = client.get('/fr/apply/')
            assert gettext("Open access compliance") == "Exigences en matière de libre accès"
            self.assertEqual(session.get('lang'), 'fr')

    def test_locale_selection(self):
        with self.app_test.test_client() as client:
            response = client.get('/apply/?lang=fr')
            self.assertEqual(session.get('lang'), 'fr')

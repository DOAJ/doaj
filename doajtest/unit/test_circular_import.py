from unittest import TestCase


class TestCircularImport(TestCase):

    def test_import__anon_import(self):
        from portality.scripts import anon_import  # noqa

    def test_import__core(self):
        from portality import core  # noqa

    def test_import__app(self):
        from portality import app  # noqa

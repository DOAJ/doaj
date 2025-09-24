import re

from faker import Faker
from freezegun import freeze_time
from copy import deepcopy

from doajtest.fixtures import AccountFixtureFactory, JournalFixtureFactory, BackgroundFixtureFactory
from doajtest.helpers import DoajTestCase
from portality import models
from portality.core import app
from portality.lib import anon
from portality.lib.anon import basic_hash, anon_name, anon_email
from portality.tasks import anon_export


class TestAnon(DoajTestCase):
    def setUp(self):
        self.old_anon_salt = app.config['ANON_SALT']
        app.config['ANON_SALT'] = 'testsalt'
        anon.fake = Faker()
        anon.fake.seed(1)

    def tearDown(self):
        app.config['ANON_SALT'] = self.old_anon_salt

    def test_01_basic_hash(self):
        assert re.match(r'x?[0-9a-f]+', basic_hash('test content'))

    def test_02_anon_name(self):
        assert anon_name() == 'Ryan Gallagher', anon_name()

    def test_03_anon_email(self):
        # Anon email should be basic_hash() + @example.com
        assert re.match(r'x?[0-9a-f]+@example\.com', anon_email('test@doaj.org'))

    def test_04_anonymise_email(self):
        record = models.Account(**AccountFixtureFactory.make_publisher_source())
        record_copy = deepcopy(record)
        e = anon_export._anonymise_email(record).email

        # Anon method changed to be a sequence
        assert e == '1@example.com', e

        # Second anon should give the same result
        e2 = anon_export._anonymise_email(record_copy).email
        assert e2 == '1@example.com', e2

        # A different email address should be #2
        reversed(record.email)
        e3 = anon_export._anonymise_email(record).email
        assert e3 == '2@example.com', e3

    def test_05_anonymise_admin_with_notes(self):
        journal_src = JournalFixtureFactory.make_journal_source()

        journal_src['admin'] = {
            'owner': 'testuser',
            'editor': 'testeditor',
            'notes': [
                {
                    "id": "note1",
                    'note': 'Test note',
                    'date': '2017-02-23T00:00:00Z',
                    'flag': {}
                },
                {
                    "id": "note2",
                    'note': 'Test note 2',
                    'date': '2017-02-23T00:00:00Z',
                    'flag': {}
                }
            ]
        }

        journal = models.Journal(**journal_src)

        with freeze_time("2017-02-23"):
            ar = anon_export._anonymise_admin(journal)

        assert ar.data['admin'] == {
            'owner': 'testuser',
            'editor': 'testeditor',
            'notes': [
                {
                    "id": "note1",
                    'note': '---note removed for data security---',
                    'date': '2017-02-23T00:00:00Z',
                    'flag': {}
                },
                {
                    "id": "note2",
                    'note': '---note removed for data security---',
                    'date': '2017-02-23T00:00:00Z',
                    'flag': {}
                }
            ]
        }, ar['admin']

    def test_06_anonymise_admin_empty_notes(self):
        journal_src = JournalFixtureFactory.make_journal_source()

        journal_src['admin'] = {
            'owner': 'testuser',
            'editor': 'testeditor',
            'notes': []
        }

        journal = models.Journal(**journal_src)

        with freeze_time("2017-02-23"):
            ar = anon_export._anonymise_admin(journal)

        assert ar.data['admin'] == {
            'owner': 'testuser',
            'editor': 'testeditor',
            'notes': []
        }, ar['admin']

    def test_07_anonymise_account(self):
        anon_a = anon_export.anonymise_account(AccountFixtureFactory.make_publisher_source())
        assert anon_a['id'] == 'publisher', anon_a['id']
        assert anon_a['email'] == '1@example.com', anon_a['email']

    def test_10_anonymise_background_job(self):
        bgjob = BackgroundFixtureFactory.example()
        bgjob['params'].update({'suggestion_bulk_edit__note': 'Test note'})
        assert re.match(r'x?[0-9a-f]+',
                        anon_export.anonymise_background_job(bgjob)['params']['suggestion_bulk_edit__note'])

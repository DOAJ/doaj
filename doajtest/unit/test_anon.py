from doajtest.helpers import DoajTestCase
from doajtest.fixtures import AccountFixtureFactory, JournalFixtureFactory, ApplicationFixtureFactory, BackgroundFixtureFactory
from portality.core import app
from portality import models
from portality.lib.anon import basic_hash, anon_name, anon_email
from portality.lib import anon
from portality.scripts import anon_export

from freezegun import freeze_time
from faker import Faker


class TestAnon(DoajTestCase):
    def setUp(self):
        self.old_anon_salt = app.config['ANON_SALT']
        app.config['ANON_SALT'] = 'testsalt'
        anon.fake = Faker()
        anon.fake.seed(1)

    def tearDown(self):
        app.config['ANON_SALT'] = self.old_anon_salt

    def test_01_basic_hash(self):
        assert basic_hash('test content') == '259ea4fab4e03a26c25f2b55f37a2f571931797d67f033e8898e76481d2a8563', basic_hash('test content')

    def test_02_anon_name(self):
        assert anon_name() == 'Ryan Gallagher', anon_name()

    def test_03_anon_email(self):
        assert anon_email('test@doaj.org') == '508dd70a7c888d9985c5ed37276d1138d73db171932b5866d48f581dc6119ac5@example.com'

    def test_04_anonymise_email(self):
        record = models.Account(**AccountFixtureFactory.make_publisher_source())
        e = anon_export._anonymise_email(record).email
        assert e == '25011d8de5bfcb72ee529fcc38b518ea6a46f99a81a412c065fe7147272b8f2a@example.com', e

    def test_05_anonymise_admin_with_notes(self):
        journal_src = JournalFixtureFactory.make_journal_source()

        journal_src['admin'] = {
            'owner': 'testuser',
            'editor': 'testeditor',
            'notes': [
                {
                    "id" : "note1",
                    'note': 'Test note',
                    'date': '2017-02-23T00:00:00Z'
                },
                {
                    "id" : "note2",
                    'note': 'Test note 2',
                    'date': '2017-02-23T00:00:00Z'
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
                    "id" : "note1",
                    'note': 'f4007b0953d4a9ecb7e31820b5d481d96ee5d74a0a059a54f07a326d357ed895',
                    'date': '2017-02-23T00:00:00Z'
                },
                {
                    "id" : "note2",
                    'note': '772cf6f91219db969e4aa28e4fd606b92316948545ad528fd34feb1b9b12a3ad',
                    'date': '2017-02-23T00:00:00Z'
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
        assert anon_a['email'] == '25011d8de5bfcb72ee529fcc38b518ea6a46f99a81a412c065fe7147272b8f2a@example.com', anon_a['email']

    def test_10_anonymise_background_job(self):
        bgjob = BackgroundFixtureFactory.example()
        bgjob['params'].update({'suggestion_bulk_edit__note': 'Test note'})
        assert anon_export.anonymise_background_job(bgjob)['params'] == {'suggestion_bulk_edit__note': 'f4007b0953d4a9ecb7e31820b5d481d96ee5d74a0a059a54f07a326d357ed895'}

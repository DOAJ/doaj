from doajtest.helpers import DoajTestCase
from portality.core import app
from portality.lib.anon import basic_hash, anon_name, anon_email
from portality.scripts import anon_export


class TestAnon(DoajTestCase):
    def setUp(self):
        self.old_anon_salt = app.config['ANON_SALT']
        app.config['ANON_SALT'] = 'testsalt'

    def tearDown(self):
        app.config['ANON_SALT'] = self.old_anon_salt

    def test_01_basic_hash(self):
        assert basic_hash('test content') == '259ea4fab4e03a26c25f2b55f37a2f571931797d67f033e8898e76481d2a8563', basic_hash('test content')

    def test_02_anon_name(self):
        assert anon_name('Tester Tester') == 'Stacy f9b6e7b982b8fc5fa95fbc024e6df9fea1ac07ad195039416bb0001fff39dde6', anon_name('Tester Tester')

    def test_03_anon_email(self):
        assert anon_email('test@doaj.org') == '508dd70a7c888d9985c5ed37276d1138d73db171932b5866d48f581dc6119ac5@example.com'

    def test_04_anonymise_email(self):
        record = {'irrelevant': 'content'}
        assert anon_export.anonymise_email(record) == {'irrelevant': 'content'}

        record = {'irrelevant': 'content', 'email': 'test@doaj.org'}
        assert anon_export.anonymise_email(record) == {'irrelevant': 'content', 'email': '508dd70a7c888d9985c5ed37276d1138d73db171932b5866d48f581dc6119ac5@example.com'}

    def test_05_anonymise_admin_with_notes(self):
        record = {'irrelevant': 'content'}
        assert anon_export.anonymise_admin(record) == {'irrelevant': 'content'}

        record = {
            'admin': {
                'owner': 'testuser',
                'editor': 'testeditor',
                'contact': {
                    'email': 'test@doaj.org',
                    'name': 'Tester Tester'
                },
                'notes': [
                    {
                        'note': 'Test note',
                        'date': '2017-02-23T14:05:34Z'
                    },
                    {
                        'note': 'Test note 2',
                        'date': '2017-02-23T14:05:34Z'
                    }
                ]
            }
        }
        assert anon_export.anonymise_admin(record) == {
            'admin': {
                'owner': 'testuser',
                'editor': 'testeditor',
                'contact': {
                    'email': '508dd70a7c888d9985c5ed37276d1138d73db171932b5866d48f581dc6119ac5@example.com',
                    'name': 'Stacy f9b6e7b982b8fc5fa95fbc024e6df9fea1ac07ad195039416bb0001fff39dde6'
                },
                'notes': [
                    {
                        'note': 'f4007b0953d4a9ecb7e31820b5d481d96ee5d74a0a059a54f07a326d357ed895',
                        'date': '2017-02-23T14:05:34Z'
                    },
                    {
                        'note': '772cf6f91219db969e4aa28e4fd606b92316948545ad528fd34feb1b9b12a3ad',
                        'date': '2017-02-23T14:05:34Z'
                    }
                ]
            }
        }

    def test_06_anonymise_admin_empty_notes(self):
        record = {
            'admin': {
                'owner': 'testuser',
                'editor': 'testeditor',
                'contact': {
                    'email': 'test@doaj.org',
                    'name': 'Tester Tester'
                },
                'notes': []
            }
        }

        assert anon_export.anonymise_admin(record) == {
            'admin': {
                'owner': 'testuser',
                'editor': 'testeditor',
                'contact': {
                    'email': '508dd70a7c888d9985c5ed37276d1138d73db171932b5866d48f581dc6119ac5@example.com',
                    'name': 'Stacy f9b6e7b982b8fc5fa95fbc024e6df9fea1ac07ad195039416bb0001fff39dde6'
                },
                'notes': []
            }
        }

    def test_07_anonymise_id(self):
        record = {'irrelevant': 'content'}
        assert anon_export.anonymise_id(record) == {'irrelevant': 'content'}

        record = {'irrelevant': 'content', 'id': 'testuser'}
        assert anon_export.anonymise_id(record) == {'irrelevant': 'content', 'id': 'a3ccf33b901b3f7ff9d005f37e734d0fe476c3ae73fcca362118a9ba84b94fd2'}

    def test_08_anonymise_account(self):
        record = {'irrelevant': 'content'}
        assert anon_export.anonymise_account(record) == {'irrelevant': 'content'}

        record = {'irrelevant': 'content', 'id': 'testuser', 'email': 'test@doaj.org'}
        assert anon_export.anonymise_account(record) == {
            'irrelevant': 'content',
            'id': 'testuser',
            'email': '508dd70a7c888d9985c5ed37276d1138d73db171932b5866d48f581dc6119ac5@example.com'
        }

    def test_08_anonymise_journal(self):
        pass  # tests 5 and 6 cover this entirely

    def test_09_anonymise_suggestion(self):
        record = {'irrelevant': 'content'}
        assert anon_export.anonymise_suggestion(record) == {'irrelevant': 'content'}

        record = {'suggestion': {'suggester': {'email': 'test@doaj.org', 'name': 'Tester Tester'}}}
        assert anon_export.anonymise_suggestion(record) == {
            'suggestion': {
                'suggester': {
                    'email': '508dd70a7c888d9985c5ed37276d1138d73db171932b5866d48f581dc6119ac5@example.com',
                    'name': 'Stacy f9b6e7b982b8fc5fa95fbc024e6df9fea1ac07ad195039416bb0001fff39dde6'
                }
            }
        }

    def test_10_anonymise_background_job(self):
        record = {'irrelevant': 'content'}
        assert anon_export.anonymise_background_job(record) == {'irrelevant': 'content'}

        record = {'params': {'suggestion_bulk_edit__note': 'Test note'}}
        assert anon_export.anonymise_background_job(record) == {'params': {'suggestion_bulk_edit__note': 'f4007b0953d4a9ecb7e31820b5d481d96ee5d74a0a059a54f07a326d357ed895'}}

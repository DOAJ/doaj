import json

from doajtest import helpers
from doajtest.fixtures import JournalFixtureFactory
from doajtest.fixtures.accounts import create_maned_a
from doajtest.helpers import DoajTestCase
from portality import models
from portality.util import url_for


class TestViewAdmin(DoajTestCase):

    def setUp(self):
        super().setUp()
        self.acc = create_maned_a(is_save=True)

    def test_journal_article_info(self):
        journal = models.Journal(
            **JournalFixtureFactory.make_journal_source()
        )
        journal.save(blocking=True)
        models.Journal.refresh()

        with self.app_test.test_client() as client:
            resp = helpers.login(client, self.acc.email, 'password')
            assert resp.status_code == 200

            resp = client.get(url_for("admin.journal_article_info", journal_id=journal.id))
            assert resp.status_code == 200
            assert json.loads(resp.data) == {'n_articles': 0}

    def test_journal_article_info__not_found(self):
        with self.app_test.test_client() as client:
            helpers.login(client, self.acc.email, 'password')

            resp = client.get(url_for("admin.journal_article_info", journal_id='aksjdlaksjdlkajsdlkajsdlk'))
            assert resp.status_code == 404

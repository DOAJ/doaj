""" Test the duplicate reporting and deletion script """

from portality.core import app
from doajtest.helpers import DoajTestCase
from doajtest.fixtures import ArticleFixtureFactory, JournalFixtureFactory, AccountFixtureFactory
from portality.scripts import article_duplicates_report_remove as a_dedupe
from portality import models

from esprit.raw import make_connection


class TestArticleMatch(DoajTestCase):

    def setUp(self):
        super(TestArticleMatch, self).setUp()

    def tearDown(self):
        super(TestArticleMatch, self).tearDown()

    def test_01_test_duplicates_global_delete_flag(self):
        """Check duplication reporting across all articles in the index"""

        # Create 2 identical articles, a duplicate pair
        article1 = models.Article(**ArticleFixtureFactory.make_article_source(
            eissn='1111-1111',
            pissn='2222-2222',
            with_id=True,
            in_doaj=True,
            with_journal_info=True
        ))
        a1_doi = article1.bibjson().get_identifiers('doi')
        assert a1_doi is not None
        article1.save(blocking=True)

        article2 = models.Article(**ArticleFixtureFactory.make_article_source(
            eissn='1111-1111',
            pissn='2222-2222',
            with_id=True,
            in_doaj=True,
            with_journal_info=True
        ))
        a2_doi = article2.bibjson().get_identifiers('doi')
        assert a2_doi == a1_doi
        article2.save(blocking=True)

        # Connect to ES with esprit and run the dedupe function without deletes
        conn = make_connection(None, app.config["ELASTIC_SEARCH_HOST"], None, app.config["ELASTIC_SEARCH_DB"])
        dupcount, delcount = a_dedupe.duplicates_per_article(conn, delete=False, snapshot=False)

        assert dupcount == 1
        assert delcount == 0

        # Run with deletes
        dupcount, delcount = a_dedupe.duplicates_per_article(conn, delete=True, snapshot=False)
        assert dupcount == 1
        assert delcount == 1

        # Check it's gone from index
        assert len(models.Article.all()) == 1

    def test_02_test_duplicates_per_account(self):
        """Check duplication reporting across all articles in the index"""

        # A publisher account
        pub_account = models.Account(**AccountFixtureFactory.make_publisher_source())
        pub_account.save()

        # The publisher has 2 journals, one in, one out of DOAJ
        in_journal = models.Journal(**JournalFixtureFactory.make_journal_source(in_doaj=True))
        in_journal.set_owner(pub_account.id)
        in_journal.save()
        out_journal = models.Journal(**JournalFixtureFactory.make_journal_source(in_doaj=False))
        out_journal.set_owner(pub_account.id)
        out_journal.save()

        pass

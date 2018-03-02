""" Test the duplicate reporting and deletion script """

from portality.core import app
from doajtest.helpers import DoajTestCase
from doajtest.fixtures import ArticleFixtureFactory, JournalFixtureFactory, AccountFixtureFactory
from portality.scripts import article_duplicates_report_remove as a_dedupe
from portality import models

from esprit.raw import make_connection

import time


class TestArticleMatch(DoajTestCase):

    def setUp(self):
        super(TestArticleMatch, self).setUp()

    def tearDown(self):
        super(TestArticleMatch, self).tearDown()

    def test_01_duplicates_global_delete_flag(self):
        """Check duplication reporting across all articles in the index"""

        # Create 2 identical articles, a duplicate pair
        article1 = models.Article(**ArticleFixtureFactory.make_article_source(
            eissn='1111-1111',
            pissn='2222-2222',
            with_id=False,
            in_doaj=True,
            with_journal_info=True
        ))
        a1_doi = article1.bibjson().get_identifiers('doi')
        assert a1_doi is not None
        article1.save(blocking=True)

        article2 = models.Article(**ArticleFixtureFactory.make_article_source(
            eissn='1111-1111',
            pissn='2222-2222',
            with_id=False,
            in_doaj=True,
            with_journal_info=True
        ))
        a2_doi = article2.bibjson().get_identifiers('doi')
        assert a2_doi == a1_doi
        article2.save(blocking=True)

        # Connect to ES with esprit and run the dedupe function without deletes
        conn = make_connection(None, app.config["ELASTIC_SEARCH_HOST"], None, app.config["ELASTIC_SEARCH_DB"])
        dupcount, delcount = a_dedupe.duplicates_per_article(conn, delete=False, snapshot=False)

        assert dupcount == 2
        assert delcount == 1                                                  # Script reports how many would be deleted
        time.sleep(0.5)
        # Check no deletes occurred
        assert len(models.Article.all()) == 2

        # Run with deletes
        dupcount, delcount = a_dedupe.duplicates_per_article(conn, delete=True, snapshot=False)
        assert dupcount == 2
        assert delcount == 1

        time.sleep(0.5)
        # Check it's gone from index
        assert len(models.Article.all()) == 1

    def test_02_duplicates_global_criteria(self):
        """ Check we match only the actual duplicates, amongst other articles in the index. """

        dup_doi = '10.xxx/xxx/bla'
        dup_fulltext = 'http://fulltext.url/article'

        # Create 12 duplicate articles with varying creation times and duplication criteria
        for i in range(1, 13):
            src_minus_identifiers = ArticleFixtureFactory.make_article_source(
                with_id=False,
                in_doaj=True,
                with_journal_info=True
            )

            del src_minus_identifiers['bibjson']['identifier']
            del src_minus_identifiers['bibjson']['link']
            article = models.Article(**src_minus_identifiers)

            # some overlapping duplication criteria - 6 have the same DOI, 4 have the same fulltext, 3 have same title
            if i % 2 == 0:
                article.bibjson().add_identifier('doi', dup_doi)
            else:
                article.bibjson().add_identifier('doi', '10.1234/' + str(i))
            if i % 3 == 0:
                article.bibjson().add_url(url=dup_fulltext, urltype='fulltext', content_type='html')
            else:
                article.bibjson().add_url('http://not_duplicate/fulltext/' + str(i), 'fulltext', 'html')
            if i % 4 == 0:
                article.bibjson().title = "This title is the same for these articles"
            else:
                article.bibjson().title = str(i) * 20
            article.save(blocking=True, differentiate=True)

        time.sleep(1.0)
        # Connect to ES with esprit and run the dedupe function
        conn = make_connection(None, app.config["ELASTIC_SEARCH_HOST"], None, app.config["ELASTIC_SEARCH_DB"])
        dupcount, delcount = a_dedupe.duplicates_per_article(conn, delete=True, snapshot=False)

        # There are 8 numbers divisible by {2,3,4} in the 12 article indexes - 2,3,4,6,8,9,12. These are our duplicates.
        assert dupcount == 8, dupcount

        # We should delete 3 of the 4 duplicates, because 4 overlap in 2 criteria (i=4, i=6, i=8, i=12).
        assert delcount == 3, delcount
        time.sleep(1.5)

        # Check how many deletes we actually had. There should be 9 left.
        assert len(models.Article.all()) == 9

    def test_03_duplicates_per_account(self):
        """ Check duplication reporting only within a publisher's account. """

        # A publisher account
        pub_account = models.Account(**AccountFixtureFactory.make_publisher_source())
        pub_account.save()

        # The publisher has 2 journals, one in, one out of DOAJ
        [j1, j2] = JournalFixtureFactory.make_many_journal_sources(2, in_doaj=True)
        in_journal = models.Journal(**j1)
        in_journal.set_owner(pub_account.id)
        in_journal.save()
        out_journal = models.Journal(**j2)
        out_journal.set_owner(pub_account.id)
        out_journal.set_in_doaj(False)
        out_journal.save(blocking=True)

        # Add some articles to the journals. First, 3 duplicates for the in_doaj journal
        for i in range(0, 3):
            article = models.Article(**ArticleFixtureFactory.make_article_source(
                with_id=False,
                in_doaj=True,
                with_journal_info=False
            ))
            article.add_journal_metadata(in_journal)                                           # Copies the ISSNs across
            article.save(differentiate=True)

        # and a not-duplicate in the in_doaj journal which should not be deleted
        art_src = ArticleFixtureFactory.make_article_source(
            with_id=False,
            in_doaj=True,
            with_journal_info=False
        )
        del art_src['bibjson']['link']
        del art_src['bibjson']['identifier']
        article_diff = models.Article(**art_src)
        article_diff.bibjson().add_url('http://not_duplicate/fulltext/_DIFFERENT', 'fulltext', 'html')
        article_diff.add_journal_metadata(in_journal)                                          # Copies the ISSNs across
        article_diff.save(blocking=True, differentiate=True)

        # Next, 2 duplicates for the not-in_doaj journals which we also expect to be taken out.
        for i in range(0, 2):
            src = ArticleFixtureFactory.make_article_source(
                with_id=False,
                in_doaj=False,
                with_journal_info=False
            )
            article = models.Article(**src)
            article.add_journal_metadata(out_journal)
            article.save(blocking=True, differentiate=True)

        # Connect to ES with esprit and run the dedupe function
        conn = make_connection(None, app.config["ELASTIC_SEARCH_HOST"], None, app.config["ELASTIC_SEARCH_DB"])
        dupcount, delcount = a_dedupe.duplicates_per_account(conn, delete=False, snapshot=False)

        assert dupcount == 5, dupcount                              # The 5 duplicates we have created across 2 journals
        assert delcount == 4, delcount                              # delete 2 from in_journal, 2 from out_journal

    def test_04_duplicates_per_account_more_publishers(self):
        """ Check duplication reporting only within a publisher's account. """
        publisher_src = AccountFixtureFactory.make_publisher_source()

        pub_account1 = models.Account(**publisher_src)
        pub_account1.save()

        publisher_src['id'] = "different_publisher"
        pub_account2 = models.Account(**publisher_src)
        pub_account2.save()

        publisher_src['id'] = "another_different_publisher"
        pub_account3 = models.Account(**publisher_src)
        pub_account3.save()

        pubs = [pub_account1, pub_account2, pub_account3]
        journs = JournalFixtureFactory.make_many_journal_sources(3, True)

        # Add a journal and a pair of duplicate articles per account
        for i in range(0, 3):
            journal = models.Journal(**journs[i])
            journal.set_owner(pubs[i].id)
            journal.save()

            for i in range(0, 2):
                article = models.Article(**ArticleFixtureFactory.make_article_source(
                    eissn=journal.known_issns()[0],
                    pissn=journal.known_issns()[1],
                    with_id=False,
                    in_doaj=False,
                    with_journal_info=True
                ))
                article.save(blocking=True, differentiate=True)

        # Connect to ES with esprit and run the dedupe function
        conn = make_connection(None, app.config["ELASTIC_SEARCH_HOST"], None, app.config["ELASTIC_SEARCH_DB"])
        dupcount, delcount = a_dedupe.duplicates_per_account(conn, delete=True, snapshot=False)

        assert dupcount == 6, dupcount                                            # 3 accounts, 2 duplicates per account
        assert delcount == 3, delcount

    def test_05_duplicates_per_account_check_separation(self):
        """ When a duplicate is across accounts, we shouldn't detect them """

        publisher_src = AccountFixtureFactory.make_publisher_source()

        pub_account1 = models.Account(**publisher_src)
        pub_account1.save()

        publisher_src['id'] = "different_publisher"
        pub_account2 = models.Account(**publisher_src)
        pub_account2.save()

        [journal1_src, journal2_src] = JournalFixtureFactory.make_many_journal_sources(2, in_doaj=True)

        journal1 = models.Journal(**journal1_src)
        journal1.set_owner(pub_account1.id)
        journal1.save()

        journal2 = models.Journal(**journal2_src)
        journal2.set_owner(pub_account2.id)
        journal2.save(blocking=True)

        assert journal1.owner != journal2.owner
        assert journal1.known_issns() != journal2.known_issns()

        # Assign duplicate articles to 2 separate journals in 2 accounts.
        article1 = models.Article(**ArticleFixtureFactory.make_article_source(
            with_id=False,
            in_doaj=False,
            with_journal_info=True
        ))
        article1.add_journal_metadata(journal1)
        article1.save(blocking=True)

        article2 = models.Article(**ArticleFixtureFactory.make_article_source(
            with_id=False,
            in_doaj=False,
            with_journal_info=True
        ))
        article2.add_journal_metadata(journal2)
        article2.save(blocking=True)

        # Connect to ES with esprit and run the dedupe function
        conn = make_connection(None, app.config["ELASTIC_SEARCH_HOST"], None, app.config["ELASTIC_SEARCH_DB"])
        dupcount, delcount = a_dedupe.duplicates_per_account(conn, delete=False, snapshot=False)

        # We expect no duplicates, since they are checked per account.
        assert dupcount == 0, dupcount
        assert delcount == 0, delcount

        # Verify we find them using the global search
        dupcount, delcount = a_dedupe.duplicates_per_article(conn, delete=False, snapshot=False)

        assert dupcount == 2, dupcount
        assert delcount == 1, delcount

    def test_06_duplication_by_title(self):
        """ We have fuzzy duplication criteria that we can also use to bolster our duplication case """
        same_title = "This is an article with the same title as another one"

        # Create 2 identical articles, a duplicate pair
        # make ourselves an example article
        a = models.Article()
        b = a.bibjson()
        b.title = same_title
        b.volume = 8
        a.save(blocking=True)

        # create another article
        a2 = models.Article()
        b2 = a.bibjson()
        b2.title = same_title
        b2.volume = 8
        a2.save(blocking=True)

        # Connect to ES with esprit and run the dedupe function without deletes
        conn = make_connection(None, app.config["ELASTIC_SEARCH_HOST"], None, app.config["ELASTIC_SEARCH_DB"])
        dupcount, delcount = a_dedupe.duplicates_per_article(conn, delete=False, snapshot=False)

        # At the moment we only have a fuzzy match, which isn't enough on its own.
        assert dupcount == 1
        assert delcount == 0  # Script reports how many would be deleted
        time.sleep(0.5)
        # Check no deletes occurred
        assert len(models.Article.all()) == 2

    def test_07_duplication_deletion_by_fuzzy(self):
        """ If the title and dois match, delete the duplicate """
        same_title = "This is an article with the same title as another one"
        same_doi = "10.1234/duplicate"

        a = models.Article()
        b = a.bibjson()
        b.title = same_title
        b.volume = 8
        b.start_page = 432
        b.add_identifier('doi', same_doi)
        a.save(blocking=True)

        a2 = models.Article()
        b2 = a2.bibjson()
        b2.title = same_title
        b2.volume = 8
        b2.start_page = 432
        b2.add_identifier('doi', same_doi)
        a2.save(blocking=True)

        # Add an article with the some similar fuzzy criteria but isn't a duplicate
        a3 = models.Article()
        b3 = a3.bibjson()
        b3.title = "this is a different title to the other articles"
        b3.volume = 8
        b3.start_page = 432
        b3.add_identifier('doi', "10.1234/non-duplicate")
        a3.save(blocking=True)

        # Connect to ES with esprit and run the dedupe function with deletes
        conn = make_connection(None, app.config["ELASTIC_SEARCH_HOST"], None, app.config["ELASTIC_SEARCH_DB"])
        dupcount, delcount = a_dedupe.duplicates_per_article(conn, delete=True, snapshot=False)
        assert dupcount == 2, dupcount                                      # Only 2 are duplicates, those with same DOI
        assert delcount == 1, delcount

        time.sleep(1.5)
        # Check it's gone from index
        assert len(models.Article.all()) == 2, len(models.Article.all())

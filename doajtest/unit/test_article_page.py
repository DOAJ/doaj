from doajtest.fixtures import ArticleFixtureFactory, JournalFixtureFactory
from doajtest.helpers import DoajTestCase
from portality import models
from portality.util import url_for


class TestArticlePage(DoajTestCase):

    def test_01_article_page_nonexistent_returns_404(self):
        """Test that a non-existent article ID returns 404 Not Found"""
        with self.app_test.test_client() as t_client:
            # Test with a UUID that doesn't exist
            fake_id = 'nonexistentarticleid123'
            response = t_client.get(url_for('doaj.article_page', identifier=fake_id))
            assert response.status_code == 404

    def test_02_article_page_tombstone_returns_410(self):
        """Test that a tombstone (deleted) article returns 410 Gone"""
        # Create a tombstone article
        source = ArticleFixtureFactory.make_article_source(in_doaj=True)
        article_id = models.Article.makeid()
        source["id"] = article_id
        tombstone = models.ArticleTombstone(**source)
        tombstone.save(blocking=True)

        with self.app_test.test_client() as t_client:
            response = t_client.get(url_for('doaj.article_page', identifier=article_id))
            assert response.status_code == 410
            # Verify it's a proper 410 page with both code and status
            assert b"410" in response.data and b"Gone" in response.data

    def test_03_article_page_withdrawn_journal_returns_410(self):
        """Test that an article from a withdrawn journal returns 410 Gone"""
        # Create a withdrawn journal (not in DOAJ)
        j_source = JournalFixtureFactory.make_journal_source(in_doaj=False)
        journal = models.Journal(**j_source)
        pissn = journal.bibjson().first_pissn
        eissn = journal.bibjson().first_eissn
        journal.save(blocking=True)

        # Create an article with this journal's ISSNs, but mark it as in_doaj=True
        # The article itself is marked in_doaj=True, but its journal is withdrawn
        a_source = ArticleFixtureFactory.make_article_source(
            pissn=pissn,
            eissn=eissn,
            in_doaj=True
        )
        article = models.Article(**a_source)
        article.save(blocking=True)

        with self.app_test.test_client() as t_client:
            response = t_client.get(url_for('doaj.article_page', identifier=article.id))
            assert response.status_code == 410
            # Verify it's a proper 410 page
            assert b"410" in response.data and b"Gone" in response.data

    def test_04_article_page_not_in_doaj_returns_410(self):
        """Test that an article marked as not in DOAJ returns 410 Gone"""
        # Create a journal in DOAJ
        j_source = JournalFixtureFactory.make_journal_source(in_doaj=True)
        journal = models.Journal(**j_source)
        pissn = journal.bibjson().first_pissn
        eissn = journal.bibjson().first_eissn
        journal.save(blocking=True)

        # Create an article that is NOT in DOAJ
        a_source = ArticleFixtureFactory.make_article_source(
            pissn=pissn,
            eissn=eissn,
            in_doaj=False  # Article itself is not in DOAJ
        )
        article = models.Article(**a_source)
        article.save(blocking=True)

        with self.app_test.test_client() as t_client:
            response = t_client.get(url_for('doaj.article_page', identifier=article.id))
            assert response.status_code == 410

    def test_05_article_page_valid_article_returns_200(self):
        """Test that a valid article in DOAJ returns 200 OK"""
        # Create a journal in DOAJ
        j_source = JournalFixtureFactory.make_journal_source(in_doaj=True)
        journal = models.Journal(**j_source)
        pissn = journal.bibjson().first_pissn
        eissn = journal.bibjson().first_eissn
        journal.save(blocking=True)

        # Create a valid article in DOAJ
        a_source = ArticleFixtureFactory.make_article_source(
            pissn=pissn,
            eissn=eissn,
            in_doaj=True
        )
        article = models.Article(**a_source)
        article.save(blocking=True)

        with self.app_test.test_client() as t_client:
            response = t_client.get(url_for('doaj.article_page', identifier=article.id))
            assert response.status_code == 200
            # Verify article content is displayed
            assert article.bibjson().title.encode() in response.data

    def test_06_article_page_journal_issn_mismatch_still_works(self):
        """Test that article page handles multiple journals with same ISSN set correctly"""
        # Create a withdrawn journal with specific ISSNs
        j1_source = JournalFixtureFactory.make_journal_source(in_doaj=False)
        j1 = models.Journal(**j1_source)
        pissn = "1234-5678"
        eissn = "8765-4321"
        j1.bibjson().pissn = pissn
        j1.bibjson().eissn = eissn
        j1.save(blocking=True)

        # Create an active journal with the same ISSNs
        j2_source = JournalFixtureFactory.make_journal_source(in_doaj=True)
        j2 = models.Journal(**j2_source)
        j2.bibjson().pissn = pissn
        j2.bibjson().eissn = eissn
        j2.save(blocking=True)

        # Create an article with these ISSNs, in DOAJ
        a_source = ArticleFixtureFactory.make_article_source(
            pissn=pissn,
            eissn=eissn,
            in_doaj=True
        )
        article = models.Article(**a_source)
        article.save(blocking=True)

        with self.app_test.test_client() as t_client:
            response = t_client.get(url_for('doaj.article_page', identifier=article.id))
            # Should succeed because one of the journals is in DOAJ
            assert response.status_code == 200


class TestErrorHandlers(DoajTestCase):
    """Test the Flask error handlers directly"""

    def test_00_400_error_handler(self):
        """Test that the 400 error handler renders the correct template"""
        with self.app_test.test_client() as t_client:
            # Test with an invalid identifier for TOC that triggers 400
            response = t_client.get(url_for('doaj.toc', identifier='invalid'))
            assert response.status_code == 400
            # Verify it renders the 400 template with both code and status text
            assert b'400' in response.data and b'Bad request' in response.data

    def test_01_404_error_handler(self):
        """Test that the 404 error handler renders the correct template"""
        with self.app_test.test_client() as t_client:
            response = t_client.get('/this-route-does-not-exist-anywhere')
            assert response.status_code == 404
            # Verify it renders the 404 template with the error code
            assert b'404' in response.data

    def test_02_article_from_withdrawn_journal_handler(self):
        """Test that ArticleFromWithdrawnJournal exception is caught and returns 410"""
        # Create a journal that's not in DOAJ
        j_source = JournalFixtureFactory.make_journal_source(in_doaj=False)
        journal = models.Journal(**j_source)
        pissn = journal.bibjson().first_pissn
        eissn = journal.bibjson().first_eissn
        journal.save(blocking=True)

        # Create an article that's technically in DOAJ but from a withdrawn journal
        a_source = ArticleFixtureFactory.make_article_source(
            pissn=pissn,
            eissn=eissn,
            in_doaj=True
        )
        article = models.Article(**a_source)
        article.save(blocking=True)

        with self.app_test.test_client() as t_client:
            response = t_client.get(url_for('doaj.article_page', identifier=article.id))
            assert response.status_code == 410
            # Verify it's a proper 410 page
            assert b'410' in response.data and b'Gone' in response.data

    def test_03_tombstone_article_handler(self):
        """Test that TombstoneArticle exception is caught and returns 410"""
        # Create a tombstone
        source = ArticleFixtureFactory.make_article_source(in_doaj=True)
        article_id = models.Article.makeid()
        source["id"] = article_id
        tombstone = models.ArticleTombstone(**source)
        tombstone.save(blocking=True)

        with self.app_test.test_client() as t_client:
            response = t_client.get(url_for('doaj.article_page', identifier=article_id))
            assert response.status_code == 410
            # Verify it's a proper 410 page
            assert b'410' in response.data and b'Gone' in response.data

    def test_04_journal_withdrawn_handler_on_toc(self):
        """Test that JournalWithdrawn exception is caught on TOC pages and returns 410"""
        import uuid
        # Create a withdrawn journal
        source = JournalFixtureFactory.make_journal_source(in_doaj=False)
        test_id = uuid.uuid4().hex
        source["id"] = test_id
        j = models.Journal(**source)
        j.save(blocking=True)

        with self.app_test.test_client() as t_client:
            response = t_client.get(url_for('doaj.toc', identifier=test_id))
            assert response.status_code == 410
            # Verify it's a proper 410 page
            assert b'410' in response.data and b'Gone' in response.data

    def test_05_error_page_renders_with_context(self):
        """Test that error pages render with proper contextual information"""
        # Test with a tombstone article to check contextual rendering
        source = ArticleFixtureFactory.make_article_source(in_doaj=True)
        article_id = models.Article.makeid()
        source["id"] = article_id
        tombstone = models.ArticleTombstone(**source)
        tombstone.save(blocking=True)

        with self.app_test.test_client() as t_client:
            response = t_client.get(url_for('doaj.article_page', identifier=article_id))
            assert response.status_code == 410
            data = response.data.decode('utf-8')
            # The error page should have contextual information about articles being removed
            # Based on error_pages.yml tombstone context, we expect both "article" AND "removed"
            assert 'article' in data.lower() and 'removed' in data.lower()

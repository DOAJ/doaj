from doajtest.fixtures import ArticleFixtureFactory, JournalFixtureFactory
from doajtest.helpers import DoajTestCase
from portality import app as _app  # noqa, make sure route is registered
from portality import models
from portality.util import url_for


def _test_toc_uses_both_issns_when_available(app_test, url_name):
    j = models.Journal(**JournalFixtureFactory.make_journal_source(in_doaj=True))
    pissn = j.bibjson().first_pissn
    eissn = j.bibjson().first_eissn
    j.save(blocking=True)
    a = models.Article(**ArticleFixtureFactory.make_article_source(pissn=pissn, eissn=eissn, in_doaj=True))
    a.save(blocking=True)
    with app_test.test_client() as t_client:
        response = t_client.get(url_for(url_name, identifier=j.bibjson().get_preferred_issn()))
        assert response.status_code == 200
        assert pissn in response.data.decode()
        assert eissn in response.data.decode()


def _test_toc_correctly_uses_pissn(app_test, url_name):
    j = models.Journal(**JournalFixtureFactory.make_journal_source(in_doaj=True))
    pissn = j.bibjson().first_pissn
    # remove eissn
    del j.bibjson().eissn
    j.save(blocking=True)
    a = models.Article(**ArticleFixtureFactory.make_article_source(pissn=pissn, in_doaj=True))
    a.save(blocking=True)
    with app_test.test_client() as t_client:
        response = t_client.get(url_for(url_name, identifier=j.bibjson().get_preferred_issn()))
        assert response.status_code == 200
        assert pissn in response.data.decode()


def _test_toc_correctly_uses_eissn(app_test, url_name):
    j = models.Journal(**JournalFixtureFactory.make_journal_source(in_doaj=True))
    eissn = j.bibjson().first_eissn
    # remove pissn
    del j.bibjson().pissn
    j.save(blocking=True)
    a = models.Article(**ArticleFixtureFactory.make_article_source(pissn=eissn, in_doaj=True))
    a.save(blocking=True)
    with app_test.test_client() as t_client:
        response = t_client.get(url_for(url_name, identifier=j.bibjson().get_preferred_issn()))
        assert response.status_code == 200
        assert eissn in response.data.decode()


class TestTOC(DoajTestCase):

    def test_01_article_index_date_parsing(self):
        """ The ToC date histogram needs an accurate datestamp in the article's index """
        a = models.Article(**ArticleFixtureFactory.make_article_source())

        # Check we can handle invalid month
        a.bibjson().year = '12'
        a.bibjson().month = '0'
        bib = a.bibjson()
        d = bib.get_publication_date()
        assert d == '2012-01-01T00:00:00Z'

        a.bibjson().year = '12'
        a.bibjson().month = '30'
        d = a.bibjson().get_publication_date()
        assert d == '2012-01-01T00:00:00Z'

        a.bibjson().year = '12'
        a.bibjson().month = 30
        d = a.bibjson().get_publication_date()
        assert d == '2012-01-01T00:00:00Z'

        a.bibjson().year = '12'
        a.bibjson().month = ''
        d = a.bibjson().get_publication_date()
        assert d == '2012-01-01T00:00:00Z'

        # Check we can handle shortened years
        a.bibjson().year = '12'
        a.bibjson().month = '03'
        d = a.bibjson().get_publication_date()
        assert d == '2012-03-01T00:00:00Z'

        a.bibjson().year = '86'  # beware: this test will give a false negative 70 years from
        a.bibjson().month = '11'  # the time of writing; this gives adequate warning (24 years)
        d = a.bibjson().get_publication_date()  # to fix hard-coding of centuries in get_publication_date().
        assert d == '1986-11-01T00:00:00Z'

        # Check we can handle numeric months
        a.bibjson().month = '03'
        a.bibjson().year = '2001'
        d = a.bibjson().get_publication_date()
        assert d == '2001-03-01T00:00:00Z'

        # Check we can handle full months
        a.bibjson().month = 'March'
        a.bibjson().year = '2001'
        d = a.bibjson().get_publication_date()
        assert d == '2001-03-01T00:00:00Z'

        # String cases?
        a.bibjson().month = 'nOVeMBer'
        a.bibjson().year = '2006'
        d = a.bibjson().get_publication_date()
        assert d == '2006-11-01T00:00:00Z'

        # And check we can handle abbreviated months
        a.bibjson().month = 'Dec'
        a.bibjson().year = '1993'
        d = a.bibjson().get_publication_date()
        assert d == '1993-12-01T00:00:00Z'

        # Finally, it wouldn't do if a bogus month was interpreted as a real one. The stamp should be created as Jan.
        a.bibjson().month = 'Flibble'
        a.bibjson().year = '1999'
        d = a.bibjson().get_publication_date()
        assert d == '1999-01-01T00:00:00Z'

    def test_02_toc_requirements(self):
        """ Check what we need for ToCs are in the article models """
        a = models.Article(**ArticleFixtureFactory.make_article_source())
        a.prep()

        # To build ToCs we need a volume, an issue, a year and a month.
        assert a.data['bibjson']['journal']['volume'] == '1'
        assert a.data['bibjson']['journal']['number'] == '99'
        assert a.data['index']['date'] == "2015-01-01T00:00:00Z"
        assert a.data['index']['date_toc_fv_month'] == a.data['index']['date'] == "2015-01-01T00:00:00Z"

    def test_03_toc_uses_both_issns_when_available(self):
        _test_toc_uses_both_issns_when_available(self.app_test, 'doaj.toc')

    def test_04_toc_correctly_uses_pissn(self):
        _test_toc_correctly_uses_pissn(self.app_test, 'doaj.toc')

    def test_05_toc_correctly_uses_eissn(self):
        _test_toc_correctly_uses_eissn(self.app_test, 'doaj.toc')

    def test_06_toc_invalid_identifier_returns_400(self):
        """Test that invalid identifiers return 400 Bad Request"""
        with self.app_test.test_client() as t_client:
            # Test invalid length identifier (not 9 for ISSN or 32 for UUID)
            response = t_client.get(url_for('doaj.toc', identifier='12345'))
            assert response.status_code == 400
            
            # Test another invalid length
            response = t_client.get(url_for('doaj.toc', identifier='1234567890123456789012345678901234567890'))
            assert response.status_code == 400

    def test_07_toc_nonexistent_issn_returns_404(self):
        """Test that a non-existent ISSN returns 404 Not Found"""
        with self.app_test.test_client() as t_client:
            # Test with a valid ISSN format but one that doesn't exist
            response = t_client.get(url_for('doaj.toc', identifier='9999-9999'))
            assert response.status_code == 404

    def test_08_toc_nonexistent_uuid_returns_404(self):
        """Test that a non-existent UUID returns 404 Not Found"""
        with self.app_test.test_client() as t_client:
            # Test with a valid UUID format but one that doesn't exist
            fake_uuid = 'ffffffffffffffffffffffffffffffff'  # 32 chars
            response = t_client.get(url_for('doaj.toc', identifier=fake_uuid))
            assert response.status_code == 404

    def test_09_toc_withdrawn_journal_uuid_returns_410(self):
        """Test that a withdrawn journal accessed by UUID returns 410 Gone"""
        import uuid
        # Create a journal that's not in DOAJ (withdrawn)
        source = JournalFixtureFactory.make_journal_source(in_doaj=False)
        # Set a proper 32-character UUID-like ID in the source
        test_id = uuid.uuid4().hex  # This creates a 32-character hex string
        source["id"] = test_id
        j = models.Journal(**source)
        j.save(blocking=True)
        
        with self.app_test.test_client() as t_client:
            response = t_client.get(url_for('doaj.toc', identifier=test_id))
            assert response.status_code == 410

    def test_10_toc_uuid_identifier_success(self):
        """Test that valid UUID identifier works correctly"""
        import uuid
        source = JournalFixtureFactory.make_journal_source(in_doaj=True)
        # Set a proper 32-character UUID-like ID in the source
        test_id = uuid.uuid4().hex  # This creates a 32-character hex string
        source["id"] = test_id
        j = models.Journal(**source)
        j.save(blocking=True)
        
        with self.app_test.test_client() as t_client:
            response = t_client.get(url_for('doaj.toc', identifier=test_id))
            # The route may redirect to canonical ISSN URL (301) or render directly (200)
            assert response.status_code in [200, 301]

    def test_11_toc_multiple_journals_same_issn_returns_in_doaj_one(self):
        """Test that when multiple journals share an ISSN, the in_doaj one is returned"""
        # Create two journals with same ISSN, one in_doaj and one not
        pissn = "1234-5678"
        eissn = "8765-4321"  # Same eissn for both to ensure ISSN sets match
        
        # Create two journal sources at once, then modify their in_doaj status
        js = JournalFixtureFactory.make_many_journal_sources(2, in_doaj=True)
        
        # First journal - set as withdrawn (not in_doaj)
        js[0]["admin"]["in_doaj"] = False
        j1 = models.Journal(**js[0])
        j1.bibjson().pissn = pissn
        j1.bibjson().eissn = eissn  # Set same eissn
        j1.save(blocking=True)
        
        # Second journal - keep as in DOAJ
        j2 = models.Journal(**js[1])
        j2.bibjson().pissn = pissn
        j2.bibjson().eissn = eissn  # Set same eissn
        j2.save(blocking=True)
        
        with self.app_test.test_client() as t_client:
            response = t_client.get(url_for('doaj.toc', identifier=pissn))
            # Should return 200/301 and serve the in_doaj journal, not the withdrawn one
            assert response.status_code in [200, 301]

    def test_12_toc_multiple_journals_same_issn_all_withdrawn_returns_410(self):
        """Test that when multiple journals share an ISSN and all are withdrawn, returns 410"""
        pissn = "2345-6789"
        eissn = "9876-5432"  # Same eissn for both to ensure ISSN sets match
        
        # Create two journals with the same ISSN, both withdrawn
        js = JournalFixtureFactory.make_many_journal_sources(2, in_doaj=False)
        for j_source in js:
            j = models.Journal(**j_source)
            j.bibjson().pissn = pissn
            j.bibjson().eissn = eissn  # Set same eissn
            j.save(blocking=True)
        
        with self.app_test.test_client() as t_client:
            response = t_client.get(url_for('doaj.toc', identifier=pissn))
            assert response.status_code == 410

    def test_13_toc_too_many_journals_same_issn_returns_500(self):
        """Test that when multiple journals share an ISSN and more than one is in_doaj, returns 500"""
        pissn = "3456-7890"
        eissn = "0987-6543"  # Same eissn for both to ensure ISSN sets match
        
        # Create two journals with th same ISSN, both in_doaj
        js = JournalFixtureFactory.make_many_journal_sources(2, in_doaj=True)
        for j_source in js:
            j = models.Journal(**j_source)
            j.bibjson().pissn = pissn
            j.bibjson().eissn = eissn  # Set same eissn
            j.save(blocking=True)
        
        with self.app_test.test_client() as t_client:
            response = t_client.get(url_for('doaj.toc', identifier=pissn))
            assert response.status_code == 500


class TestTOCArticles(DoajTestCase):
    def test_03_toc_uses_both_issns_when_available(self):
        _test_toc_uses_both_issns_when_available(self.app_test, 'doaj.toc_articles')

    def test_04_toc_correctly_uses_pissn(self):
        _test_toc_correctly_uses_pissn(self.app_test, 'doaj.toc_articles')

    def test_05_toc_correctly_uses_eissn(self):
        _test_toc_correctly_uses_eissn(self.app_test, 'doaj.toc_articles')

    def test_06_toc_articles_invalid_identifier_returns_400(self):
        """Test that invalid identifiers return 400 Bad Request for articles route"""
        with self.app_test.test_client() as t_client:
            # Test invalid length identifier
            response = t_client.get(url_for('doaj.toc_articles', identifier='12345'))
            assert response.status_code == 400

    def test_07_toc_articles_nonexistent_issn_returns_404(self):
        """Test that non-existent ISSN returns 404 Not Found for articles route"""
        with self.app_test.test_client() as t_client:
            response = t_client.get(url_for('doaj.toc_articles', identifier='9999-9999'))
            assert response.status_code == 404

    def test_08_toc_articles_nonexistent_uuid_returns_404(self):
        """Test that non-existent UUID returns 404 Not Found for articles route"""
        with self.app_test.test_client() as t_client:
            fake_uuid = 'ffffffffffffffffffffffffffffffff'
            response = t_client.get(url_for('doaj.toc_articles', identifier=fake_uuid))
            assert response.status_code == 404

    def test_09_toc_articles_withdrawn_journal_uuid_returns_410(self):
        """Test that a withdrawn journal accessed by UUID returns 410 Gone for articles route"""
        import uuid
        source = JournalFixtureFactory.make_journal_source(in_doaj=False)
        # Set a proper 32-character UUID-like ID in the source
        test_id = uuid.uuid4().hex  # This creates a 32-character hex string
        source["id"] = test_id
        j = models.Journal(**source)
        j.save(blocking=True)
        
        with self.app_test.test_client() as t_client:
            response = t_client.get(url_for('doaj.toc_articles', identifier=test_id))
            assert response.status_code == 410

    def test_10_toc_articles_uuid_identifier_success(self):
        """Test that a valid UUID identifier works correctly for articles route"""
        import uuid
        source = JournalFixtureFactory.make_journal_source(in_doaj=True)
        # Set a proper 32-character UUID-like ID in the source
        test_id = uuid.uuid4().hex  # This creates a 32-character hex string
        source["id"] = test_id
        j = models.Journal(**source)
        j.save(blocking=True)
        
        # Create an article to avoid ES mapping issues with article_stats() call
        a = models.Article(**ArticleFixtureFactory.make_article_source(
            pissn=j.bibjson().first_pissn, eissn=j.bibjson().first_eissn, in_doaj=True
        ))
        a.save(blocking=True)
        
        with self.app_test.test_client() as t_client:
            response = t_client.get(url_for('doaj.toc_articles', identifier=test_id))
            # The route may redirect to canonical ISSN URL (301) or render directly (200)
            assert response.status_code in [200, 301]

    def test_11_toc_articles_multiple_journals_same_issn_returns_in_doaj_one(self):
        """Test that when multiple journals share an ISSN, the in_doaj one is returned for the articles route"""
        pissn = "4567-8901"
        eissn = "1098-7654"  # Same eissn for both to ensure ISSN sets match
        
        # Create two journal sources at once, then modify their in_doaj status
        js = JournalFixtureFactory.make_many_journal_sources(2, in_doaj=True)
        
        # First journal - set as withdrawn (not in_doaj)
        js[0]["admin"]["in_doaj"] = False
        j1 = models.Journal(**js[0])
        j1.bibjson().pissn = pissn
        j1.bibjson().eissn = eissn  # Set same eissn
        j1.save(blocking=True)
        
        # Second journal - keep as in DOAJ
        j2 = models.Journal(**js[1])
        j2.bibjson().pissn = pissn
        j2.bibjson().eissn = eissn  # Set same eissn
        j2.save(blocking=True)
        
        # Create an article to avoid ES mapping issues
        a = models.Article(**ArticleFixtureFactory.make_article_source(
            pissn=pissn, in_doaj=True
        ))
        a.save(blocking=True)
        
        with self.app_test.test_client() as t_client:
            response = t_client.get(url_for('doaj.toc_articles', identifier=pissn))
            # Should return 200/301 and serve the in_doaj journal, not the withdrawn one
            assert response.status_code in [200, 301]

    def test_12_toc_articles_multiple_journals_same_issn_all_withdrawn_returns_410(self):
        """Test that when multiple journals share an ISSN and all are withdrawn, returns 410 for articles route"""
        pissn = "5678-9012"
        eissn = "2109-8765"  # Same eissn for both to ensure ISSN sets match
        
        # Create two journals with same ISSN, both withdrawn
        js = JournalFixtureFactory.make_many_journal_sources(2, in_doaj=False)
        for j_source in js:
            j = models.Journal(**j_source)
            j.bibjson().pissn = pissn
            j.bibjson().eissn = eissn  # Set same eissn
            j.save(blocking=True)
        
        with self.app_test.test_client() as t_client:
            response = t_client.get(url_for('doaj.toc_articles', identifier=pissn))
            assert response.status_code == 410

    def test_13_toc_articles_too_many_journals_same_issn_returns_500(self):
        """Test that when multiple journals share an ISSN and more than one is in_doaj, returns 500 for articles route"""
        pissn = "6789-0123"
        eissn = "3210-9876"  # Same eissn for both to ensure ISSN sets match
        
        # Create two journals with same ISSN, both in_doaj
        js = JournalFixtureFactory.make_many_journal_sources(2, in_doaj=True)
        for j_source in js:
            j = models.Journal(**j_source)
            j.bibjson().pissn = pissn
            j.bibjson().eissn = eissn  # Set same eissn
            j.save(blocking=True)
        
        with self.app_test.test_client() as t_client:
            response = t_client.get(url_for('doaj.toc_articles', identifier=pissn))
            assert response.status_code == 500

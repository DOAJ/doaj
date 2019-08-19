from doajtest.helpers import DoajTestCase
from doajtest.fixtures import DoajXmlArticleFixtureFactory, JournalFixtureFactory
from portality import models


class TestTOC(DoajTestCase):

    def setUp(self):
        super(TestTOC, self).setUp()

    def tearDown(self):
        super(TestTOC, self).tearDown()

    def test_01_article_index_date_parsing(self):
        """ The ToC date histogram needs an accurate datestamp in the article's index """
        a = models.Article(**DoajXmlArticleFixtureFactory.make_article_source())

        # Check we can handle shortened years
        a.bibjson().year = '12'
        a.bibjson().month = '03'
        d = a.bibjson().get_publication_date()
        assert d == '2012-03-01T00:00:00Z'

        a.bibjson().year = '86'                            # beware: this test will give a false negative 70 years from
        a.bibjson().month = '11'                           # the time of writing; this gives adequate warning (24 years)
        d = a.bibjson().get_publication_date()             # to fix hard-coding of centuries in get_publication_date().
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
        a = models.Article(**DoajXmlArticleFixtureFactory.make_article_source())
        a.prep()

        # To build ToCs we need a volume, an issue, a year and a month.
        assert a.data['bibjson']['journal']['volume'] == '1'
        assert a.data['bibjson']['journal']['number'] == '99'
        assert a.data['index']['date'] == "1991-01-01T00:00:00Z"
        assert a.data['index']['date_toc_fv_month'] == a.data['index']['date'] == "1991-01-01T00:00:00Z"

    def test_03_toc_uses_both_issns_when_available(self):
        j = models.Journal(**JournalFixtureFactory.make_journal_source(in_doaj=True))
        pissn = j.bibjson().first_pissn
        eissn = j.bibjson().first_eissn
        j.set_last_manual_update()
        j.save(blocking=True)
        a = models.Article(**DoajXmlArticleFixtureFactory.make_article_source(pissn=pissn, eissn=eissn, in_doaj=True))
        a.save(blocking=True)
        with self.app_test.test_client() as t_client:
            response = t_client.get('/toc/{}'.format(j.bibjson().get_preferred_issn()))
            assert response.status_code == 200
            assert 'var toc_issns = ["{pissn}","{eissn}"];'.format(pissn=pissn, eissn=eissn) in response.data

    def test_04_toc_correctly_uses_pissn(self):
        j = models.Journal(**JournalFixtureFactory.make_journal_source(in_doaj=True))
        pissn = j.bibjson().first_pissn
        # remove eissn
        j.bibjson().remove_identifiers(idtype=j.bibjson().E_ISSN, id=j.bibjson().first_eissn)

        j.set_last_manual_update()
        j.save(blocking=True)
        a = models.Article(**DoajXmlArticleFixtureFactory.make_article_source(pissn=pissn, in_doaj=True))
        a.save(blocking=True)
        with self.app_test.test_client() as t_client:
            response = t_client.get('/toc/{}'.format(j.bibjson().get_preferred_issn()))
            assert response.status_code == 200
            assert 'var toc_issns = ["{pissn}"];'.format(pissn=pissn) in response.data

    def test_05_toc_correctly_uses_eissn(self):
        j = models.Journal(**JournalFixtureFactory.make_journal_source(in_doaj=True))
        eissn = j.bibjson().first_eissn
        # remove pissn
        j.bibjson().remove_identifiers(idtype=j.bibjson().P_ISSN, id=j.bibjson().first_pissn)

        j.set_last_manual_update()
        j.save(blocking=True)
        a = models.Article(**DoajXmlArticleFixtureFactory.make_article_source(pissn=eissn, in_doaj=True))
        a.save(blocking=True)
        with self.app_test.test_client() as t_client:
            response = t_client.get('/toc/{}'.format(j.bibjson().get_preferred_issn()))
            assert response.status_code == 200
            assert 'var toc_issns = ["{eissn}"];'.format(eissn=eissn) in response.data

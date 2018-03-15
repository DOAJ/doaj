from doajtest.helpers import DoajTestCase
from portality import article, models
from doajtest.fixtures import ArticleFixtureFactory
import uuid, time
from random import randint
from copy import deepcopy


class TestArticleMatch(DoajTestCase):

    def setUp(self):
        super(TestArticleMatch, self).setUp()

    def tearDown(self):
        super(TestArticleMatch, self).tearDown()

    def test_01_same_fulltext(self):
        """Check duplication detection on articles with the same fulltext URL"""

        # A list of various URLs to check matching on
        ftus = [
            "http://examplejournal.telfor.rs/Published/Vol1No1/Vol1No1_A5.pdf",
            "http://www.sbe.deu.edu.tr/dergi/cilt15.say%C4%B12/06%20AKALIN.pdf",
            "http://www.ujcem.med.sumdu.edu.ua/images/sampledata/2013/4/408_412_IV-020.pdf",
            "http://www.psychologie-aktuell.com/fileadmin/download/ptam/1-2014_20140324/01_Geiser.pdf"
        ]

        for ftu in ftus:
            # make ourselves an example article
            a = models.Article()
            b = a.bibjson()
            b.title = "Example article with a fulltext url"
            b.add_url(ftu, urltype="fulltext")
            a.save(blocking=True)

            # create a replacement article
            z = models.Article()
            y = z.bibjson()
            y.title = "Replacement article for fulltext url"
            y.add_url(ftu, urltype="fulltext")

            # get the xwalk to determine if there is a duplicate
            xwalk = article.XWalk()
            d = xwalk.get_duplicate(z)

            assert d is not None
            assert d.bibjson().title == "Example article with a fulltext url"
        
    def test_02_different_fulltext(self):
        """Check that an article with different fulltext URLs is not considered a duplicate"""
        # make ourselves an example article
        a = models.Article()
        b = a.bibjson()
        b.title = "Example 2 article with a fulltext url"
        b.add_url("http://www.sbe.deu.edu.tr/dergi/cilt15.say%C4%B12/06%20AKALIN.pdf", urltype="fulltext")
        a.save(blocking=True)

        # create another article
        z = models.Article()
        y = z.bibjson()
        y.title = "Replacement article for fulltext url"
        y.add_url("http://this.is/a/different/url", urltype="fulltext")
        
        # get the xwalk to determine if there is a duplicate
        xwalk = article.XWalk()
        d = xwalk.get_duplicate(z)
        
        assert d is None
    
    def test_03_retrieve_latest(self):

        ftu = "http://www.sbe.deu.edu.tr/dergi/cilt15.say%C4%B12/06%20AKALIN.pdf"
        # make ourselves a couple of example articles
        a = models.Article()
        b = a.bibjson()
        b.title = "Example A article with a fulltext url"
        b.add_url(ftu, urltype="fulltext")
        a.save()
        
        # wait for a bit to create good separation between last_updated times
        time.sleep(1.3)
        
        a2 = models.Article()
        b2 = a2.bibjson()
        b2.title = "Example B article with a fulltext url"
        b2.add_url(ftu, urltype="fulltext")
        a2.save()

        # wait for a bit to create good separation between last_updated times
        time.sleep(1.3)

        # create an article which should not be caught by the duplicate detection
        not_duplicate = models.Article()
        not_duplicate_bibjson = not_duplicate.bibjson()
        not_duplicate_bibjson.title = "Example C article with a fulltext url"
        not_duplicate_bibjson.add_url("http://this.is/a/different/url", urltype="fulltext")
        not_duplicate.save(blocking=True)
        
        # create a replacement article
        z = models.Article()
        y = z.bibjson()
        y.title = "Replacement article for fulltext url"
        y.add_url(ftu, urltype="fulltext")
        
        # get the xwalk to determine if there is a duplicate
        xwalk = article.XWalk()
        d = xwalk.get_duplicate(z)

        # Check when we ask for one duplicate we get the most recent duplicate.
        assert d is not None
        assert d.bibjson().title == "Example B article with a fulltext url", d.bibjson().title

        # get the xwalk to determine all duplicates
        # sort both results and expectations here to avoid false alarm
        # we don't care about the order of duplicates
        expected = sorted([a, a2])
        xwalk = article.XWalk()
        l = xwalk.get_duplicates(z)
        assert isinstance(l, list), l
        assert l
        l.sort()
        assert expected == l

    def test_04_with_doi_instead(self):
        """Detect a duplicate using the DOI field."""
        # make ourselves a couple of example articles
        a = models.Article()
        b = a.bibjson()
        b.title = "Example A article with a DOI"
        b.add_identifier('doi', "10.doi")
        a.save()

        # wait for a bit to create good separation between last_updated times
        time.sleep(1.3)

        a2 = models.Article()
        b2 = a2.bibjson()
        b2.title = "Example B article with a DOI"
        b2.add_identifier('doi', "10.doi")
        a2.save()

        # wait for a bit to create good separation between last_updated times
        time.sleep(1.3)

        # create an article which should not be caught by the duplicate detection
        not_duplicate = models.Article()
        not_duplicate_bibjson = not_duplicate.bibjson()
        not_duplicate_bibjson.title = "Example C article with a DOI"
        not_duplicate_bibjson.add_identifier('doi', "10.doi.DIFFERENT")
        not_duplicate.save(blocking=True)

        # create a replacement article
        z = models.Article()
        y = z.bibjson()
        y.title = "Replacement article for fulltext url"
        y.add_identifier('doi', "10.doi")

        # get the xwalk to determine if there is a duplicate
        xwalk = article.XWalk()
        d = xwalk.get_duplicate(z)

        # Check when we ask for one duplicate we get the most recent duplicate.
        assert d is not None
        assert d.bibjson().title == "Example B article with a DOI", d.bibjson().title

        # get the xwalk to determine all duplicates
        # sort both results and expectations here to avoid false alarm
        # we don't care about the order of duplicates
        expected = sorted([a, a2])
        xwalk = article.XWalk()
        l = xwalk.get_duplicates(z)
        assert isinstance(l, list)
        assert l
        assert len(l) == 2
        l.sort()
        assert expected == l
    
    def test_05_merge_replaces_metadata(self):
        """Ensure that merging replaces metadata of a new article, but keeps its old id."""

        ftu = "http://www.sbe.deu.edu.tr/dergi/cilt15.say%C4%B12/06%20AKALIN.pdf"
        id1 = uuid.uuid4().hex
        id2 = uuid.uuid4().hex
        assert id1 != id2

        a = models.Article()
        a.set_id(id1)
        b = a.bibjson()
        b.title = "Example A article with a fulltext url"
        b.abstract = "a bunch of text"
        b.add_url(ftu, urltype="fulltext")

        a2 = models.Article()
        a2.set_id(id2)
        b2 = a2.bibjson()
        b2.title = "Example B article with a fulltext url"
        b2.add_url(ftu, urltype="fulltext")

        # perform a merge, which updates article records of a2 based on a - including the id.
        assert a2.id == id2
        a2.merge(a)
        assert a2.id == id1

        # Check that we have the newer metadata
        assert a2.bibjson().title == "Example B article with a fulltext url"
        assert a2.bibjson().abstract is None

        # Create a 3rd article without an explicit id
        a3 = models.Article()
        b3 = a3.bibjson()
        b3.title = "Example C article with a fulltext url"
        b3.abstract = "a newer bunch of text"
        b3.add_url(ftu, urltype="fulltext")

        a3.merge(a2)

        assert a3.id == a2.id == a.id
        assert a3.bibjson().title == "Example C article with a fulltext url"
        assert a3.bibjson().abstract == "a newer bunch of text"

    def test_06_both_duplication_criteria(self):
        """Check that an article is only reported once if it is duplicated by both DOI and fulltext URL"""
        # make ourselves an example article
        ftu = "http://www.sbe.deu.edu.tr/dergi/cilt15.say%C4%B12/06%20AKALIN.pdf"
        doi = "10.doi"

        a = models.Article()
        b = a.bibjson()
        b.title = "Example article with a fulltext url and a DOI"
        b.add_url(ftu, urltype="fulltext")
        b.add_identifier('doi', doi)
        a.save(blocking=True)

        # create another article
        z = models.Article()
        y = z.bibjson()
        y.title = "Replacement article for fulltext url and a DOI"
        y.add_url(ftu, urltype="fulltext")
        y.add_identifier('doi', doi)

        # get the xwalk to determine if there is a duplicate
        xwalk = article.XWalk()
        d = xwalk.get_duplicates(z)

        assert len(d) == 1
        print len(d)
        assert d[0].bibjson().title == "Example article with a fulltext url and a DOI"

    def test_07_many_issns(self):
        """Test that a query with a LOT of ISSNs is still successful."""
        a = models.Article()
        b = a.bibjson()
        b.journal_issns = ["0000-0000"]
        b.title = "Example A article with a fulltext url"
        b.add_identifier(b.DOI, "10.1234/duplicate")
        a.save(blocking=True)

        def random_issn():
            bits = []
            for i in range(8):
                bits.append(str(randint(1, 9)))
            return "".join(bits[:4]) + "-" + "".join(bits[4:])

        issns = [random_issn() for _ in range(2000)] + ["0000-0000"]

        dupes = models.Article.duplicates(issns=issns, doi="10.1234/duplicate")
        assert len(dupes) == 1

    def test_08_same_title(self):
        """Check that an article with the same title is considered a duplicate"""
        same_title = "Example article title"

        # make ourselves an example article
        a = models.Article()
        b = a.bibjson()
        b.title = same_title
        a.save(blocking=True)

        # create another article
        z = models.Article()
        y = z.bibjson()
        y.title = same_title

        # get the xwalk to determine if there is a duplicate
        xwalk = article.XWalk()
        d = xwalk.get_duplicate(z)

        assert d is not None

    def test_09_similar_title(self):
        """Check that an article can have the same title but not be considered a duplicate"""
        # make ourselves an example article
        a = models.Article()
        b = a.bibjson()
        b.title = "This article is about things like cheese"
        a.save(blocking=True)

        # create another article
        a2 = models.Article()
        b2 = a.bibjson()
        b2.title = "This article is about things like flamboyance"
        a2.save(blocking=True)

        # And a third
        z = models.Article()
        y = z.bibjson()
        y.title = "About cheese is things like this article"

        # get the xwalk to determine if there is a duplicate
        xwalk = article.XWalk()
        d = xwalk.get_duplicate(z)

        assert d is None, d

    def test_10_article_replace_strong_criteria(self):
        """ Have a detailed look at the article duplication detection """
        # Get ourselves a fully populated article
        a = models.Article(**ArticleFixtureFactory.make_article_source())
        a.save(blocking=True)

        b_copy = deepcopy(a.data)
        del b_copy['id']
        b = models.Article(**b_copy)

        # We can change the ISSN or fulltext URL and it's still a duplicate - first, the DOI is differentiated
        b.bibjson().remove_identifiers()
        b_doi = "10.doi_for_article_b"
        b.bibjson().add_identifier('doi', b_doi)

        # Check that the saved article is a duplicate
        dups = article.XWalk.get_duplicates(b)
        assert len(dups) == 1
        assert dups[0].id == a.id

        # A different fulltext, but the DOI is still the same.
        c_copy = deepcopy(a.data)
        del c_copy['id']
        c = models.Article(**c_copy)
        del c.data['bibjson']['link']
        assert c.bibjson().get_single_url('fulltext') is None
        c.bibjson().add_url("http://url_for.article_c", urltype="fulltext")
        assert c.bibjson().get_single_url('fulltext') == "http://url_for.article_c"
        assert c.bibjson().get_one_identifier('doi') == a.bibjson().get_one_identifier('doi')

        # Check that the saved article is a duplicate
        dups = article.XWalk.get_duplicates(c)
        assert len(dups) == 1, len(dups)
        assert dups[0].id == a.id

        # If those duplicates are saved too, we should have more to find in the index when we check again
        b.save(blocking=True)
        c.save(blocking=True)

        x_copy = deepcopy(a.data)
        del x_copy['id']
        x = models.Article(**x_copy)
        dups = article.XWalk.get_duplicates(x)
        assert len(dups) == 3

        # Check that we get the same results when there's more stuff in the index than our duplicates.
        for i in range(0, 5):
            unique_issn = '{0}-{1}'.format(str(i) * 4, str(i)*4)
            art = models.Article(**ArticleFixtureFactory.make_article_source(eissn=unique_issn, pissn=unique_issn, with_id=False, with_journal_info=True))
            art.bibjson().remove_identifiers('doi')
            art.bibjson().add_identifier('doi', '10.doi_for_article_' + str(i))
            art.bibjson().title = str(i) * 12
            del art.data['bibjson']['link']
            art.bibjson().add_url("http://url_for.article_" + str(i), urltype="fulltext")
            art.bibjson().start_page = i
            art.save(blocking=True)

        dups = article.XWalk.get_duplicates(x)
        assert len(dups) == 3

    def test_11_article_replace_weak_criteria(self):

        # Get ourselves a fully populated article
        a = models.Article(**ArticleFixtureFactory.make_article_source())
        a.save(blocking=True)

        b_copy = deepcopy(a.data)
        del b_copy['id']
        b = models.Article(**b_copy)

        # Change both DOI and fulltext URL, won't overwrite - we require one of those as well as the fuzzy criteria
        del b.data['bibjson']['link']
        b.bibjson().add_url("http://url_for.article_b", urltype="fulltext")
        b.bibjson().remove_identifiers()
        b.bibjson().add_identifier('doi', "10.doi_for_article_b")

        # We have 2 matching criteria for our fuzzy match, so it should pass.
        assert a.bibjson().title == b.bibjson().title
        assert a.bibjson().start_page == b.bibjson().start_page

        # Verify it was detected as a fuzzy match
        dups = article.XWalk.discover_duplicates(b)
        assert dups['doi'] is None
        assert dups['fulltext'] is None
        assert dups['fuzzy'] is not None
        assert len(dups['fuzzy']) == 1
        assert dups['fuzzy'].pop()['id'] == a.id

        # However, we expect the overall duplication to return none because we require more than just fuzzy
        dups = article.XWalk.get_duplicates(b)
        assert len(dups) == 0

        # Another article, with no matching criteria - not a duplicate
        c_copy = deepcopy(a.data)
        del c_copy['id']
        c = models.Article(**c_copy)

        # Change some of the metadata to make it sufficiently different and be a new article.
        del c.data['bibjson']['link']
        c.bibjson().add_url("http://url_for.article_e", urltype="fulltext")
        c.bibjson().remove_identifiers()
        c.bibjson().add_identifier('doi', "10.doi_for_article_e")
        c.bibjson().add_identifier('pissn', a.bibjson().first_pissn)
        c.bibjson().add_identifier('eissn', a.bibjson().first_eissn)

        # Add a different title and start page - only the ISSN matches now.
        c.bibjson().title = "This title is distinct from the others"
        c.bibjson().start_page = 321
        assert c.bibjson().start_page != a.bibjson().start_page

        print models.Article.all()
        assert c.id != a.id

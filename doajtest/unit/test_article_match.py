from doajtest.helpers import DoajTestCase
from portality import models
import uuid, time
from random import randint
from portality.bll.doaj import DOAJ

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

            # determine if there's a duplicate
            articleService = DOAJ.articleService()
            d = articleService.get_duplicate(z)

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
        
        # determine if there's a duplicate
        articleService = DOAJ.articleService()
        d = articleService.get_duplicate(z)
        
        assert d is None
    
    def test_03_retrieve_latest(self):

        ftu = "http://www.sbe.deu.edu.tr/dergi/cilt15.say%C4%B12/06%20AKALIN.pdf"
        # make ourselves a couple of example articles
        a = models.Article()
        b = a.bibjson()
        b.title = "Example A article with a fulltext url"
        b.add_url(ftu, urltype="fulltext")
        a.save(blocking=True)

        # Wait a second to ensure the timestamps are different
        time.sleep(1.01)
        
        a2 = models.Article()
        b2 = a2.bibjson()
        b2.title = "Example B article with a fulltext url"
        b2.add_url(ftu, urltype="fulltext")
        a2.save(blocking=True)

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
        
        # determine if there's a duplicate
        articleService = DOAJ.articleService()
        d = articleService.get_duplicate(z)

        # Check when we ask for one duplicate we get the most recent duplicate.
        assert d is not None
        assert d.bibjson().title == "Example B article with a fulltext url", d.bibjson().title

        # get the xwalk to determine all duplicates
        # sort both results and expectations here to avoid false alarm
        # we don't care about the order of duplicates
        expected = sorted([a, a2])
        # determine if there's a duplicate
        l = articleService.get_duplicates(z)
        assert isinstance(l, list), l
        assert l is not None
        l.sort()
        assert expected == l

    def test_04_with_doi_instead(self):
        """Detect a duplicate using the DOI field."""
        # make ourselves a couple of example articles
        a = models.Article()
        b = a.bibjson()
        b.title = "Example A article with a DOI"
        b.add_identifier('doi', "10.doi/123")
        a.save(blocking=True)

        # Wait a second to ensure the timestamps are different
        time.sleep(1.01)

        a2 = models.Article()
        b2 = a2.bibjson()
        b2.title = "Example B article with a DOI"
        b2.add_identifier('doi', "10.doi/123")
        a2.save(blocking=True)

        # create an article which should not be caught by the duplicate detection
        not_duplicate = models.Article()
        not_duplicate_bibjson = not_duplicate.bibjson()
        not_duplicate_bibjson.title = "Example C article with a DOI"
        not_duplicate_bibjson.add_identifier('doi', "10.doi/DIFFERENT")
        not_duplicate.save(blocking=True)

        # create a replacement article
        z = models.Article()
        y = z.bibjson()
        y.title = "Replacement article for DOI"
        y.add_identifier('doi', "10.doi/123")

        # determine if there's a duplicate
        articleService = DOAJ.articleService()
        dups = articleService.get_duplicates(z)
        assert len(dups) == 2

        # Check when we ask for one duplicate we get the most recent duplicate.
        d = articleService.get_duplicate(z)
        assert d is not None
        assert d.bibjson().title == "Example B article with a DOI", d.bibjson().title

        # get the xwalk to determine all duplicates
        # sort both results and expectations here to avoid false alarm
        # we don't care about the order of duplicates
        expected = sorted([a, a2])
        # determine if there's a duplicate
        l = articleService.get_duplicates(z)
        assert isinstance(l, list)
        assert l
        assert len(l) == 2
        l.sort()
        assert expected == l

    def test_05_full_doi(self):
        """ Test that we still detect duplicate DOIs when we have the full URI, not just the 10. """
        # make ourselves a couple of example articles
        a = models.Article()
        b = a.bibjson()
        b.title = "Example A article with a DOI"
        b.add_identifier('doi', "https://doi.org/10.doi/123")
        a.save(blocking=True)

        # Wait a second to ensure the timestamps are different
        time.sleep(1.01)

        a2 = models.Article()
        b2 = a2.bibjson()
        b2.title = "Example B article with a DOI"
        b2.add_identifier('doi', "https://doi.org/10.doi/123")
        a2.save(blocking=True)

        # create an article which should not be caught by the duplicate detection
        not_duplicate = models.Article()
        not_duplicate_bibjson = not_duplicate.bibjson()
        not_duplicate_bibjson.title = "Example C article with a DOI"
        not_duplicate_bibjson.add_identifier('doi', "https://doi.org/10.doi/DIFFERENT")
        not_duplicate.save(blocking=True)

        # create a replacement article
        z = models.Article()
        y = z.bibjson()
        y.title = "Replacement article for DOI"
        y.add_identifier('doi', "https://doi.org/10.doi/123")

        # determine if there's a duplicate
        articleService = DOAJ.articleService()
        dups = articleService.get_duplicates(z)
        assert len(dups) == 2

        # Check when we ask for one duplicate we get the most recent duplicate.
        d = articleService.get_duplicate(z)
        assert d is not None
        assert d.bibjson().title == "Example B article with a DOI", d.bibjson().title
    
    def test_06_merge_replaces_metadata(self):
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

    def test_07_both_duplication_criteria(self):
        """Check that an article is only reported once if it is duplicated by both DOI and fulltext URL"""
        # make ourselves an example article
        ftu = "http://www.sbe.deu.edu.tr/dergi/cilt15.say%C4%B12/06%20AKALIN.pdf"
        doi = "10.doi/123"

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

        # determine if there's a duplicate
        articleService = DOAJ.articleService()
        d = articleService.get_duplicates(z)

        assert len(d) == 1
        print len(d)
        assert d[0].bibjson().title == "Example article with a fulltext url and a DOI"

    def test_08_many_issns(self):
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

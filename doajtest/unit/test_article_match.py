from doajtest.helpers import DoajTestCase
from portality import article, models
import uuid, time
from random import randint

class TestArticleMatch(DoajTestCase):

    def setUp(self):
        super(TestArticleMatch, self).setUp()

    def tearDown(self):
        super(TestArticleMatch, self).tearDown()

    def test_01(self):
        # make ourselves an example article
        a = models.Article()
        b = a.bibjson()
        b.title = "Example article with a fulltext url"
        b.add_url("http://examplejournal.telfor.rs/Published/Vol1No1/Vol1No1_A5.pdf", urltype="fulltext")
        a.save()
        
        # pause to allow the index time to catch up
        time.sleep(2)
        
        # create a replacement article
        z = models.Article()
        y = z.bibjson()
        y.title = "Replacement article for fulltext url"
        y.add_url("http://examplejournal.telfor.rs/Published/Vol1No1/Vol1No1_A5.pdf", urltype="fulltext")
        
        # get the xwalk to determine if there is a duplicate
        xwalk = article.XWalk()
        d = xwalk.get_duplicate(z)
        
        assert d is not None
        assert d.bibjson().title == "Example article with a fulltext url"
        
    def test_02(self):
        # make ourselves an example article
        a = models.Article()
        b = a.bibjson()
        b.title = "Example 2 article with a fulltext url"
        b.add_url("http://www.sbe.deu.edu.tr/dergi/cilt15.say%C4%B12/06%20AKALIN.pdf", urltype="fulltext")
        a.save()
        
        # pause to allow the index time to catch up
        time.sleep(2)
        
        # create a replacement article
        z = models.Article()
        y = z.bibjson()
        y.title = "Replacement article for fulltext url"
        y.add_url("http://www.sbe.deu.edu.tr/dergi/cilt15.say%C4%B12/06%20AKALIN.pdf", urltype="fulltext")
        
        # get the xwalk to determine if there is a duplicate
        xwalk = article.XWalk()
        d = xwalk.get_duplicate(z)
        
        assert d is not None
        assert d.bibjson().title == "Example 2 article with a fulltext url"
    
    def test_03(self):
        # make ourselves an example article
        a = models.Article()
        b = a.bibjson()
        b.title = "Example 2 article with a fulltext url"
        b.add_url("http://www.ujcem.med.sumdu.edu.ua/images/sampledata/2013/4/408_412_IV-020.pdf", urltype="fulltext")
        a.save()
        
        # pause to allow the index time to catch up
        time.sleep(2)
        
        # create a replacement article
        z = models.Article()
        y = z.bibjson()
        y.title = "Replacement article for fulltext url"
        y.add_url("http://www.ujcem.med.sumdu.edu.ua/images/sampledata/2013/4/408_412_IV-020.pdf", urltype="fulltext")
        
        # get the xwalk to determine if there is a duplicate
        xwalk = article.XWalk()
        d = xwalk.get_duplicate(z)
        
        assert d is not None
        assert d.bibjson().title == "Example 2 article with a fulltext url"
    
    def test_04(self):
        # make ourselves an example article
        a = models.Article()
        b = a.bibjson()
        b.title = "Example 2 article with a fulltext url"
        b.add_url("http://www.psychologie-aktuell.com/fileadmin/download/ptam/1-2014_20140324/01_Geiser.pdf", urltype="fulltext")
        a.save()
        
        # pause to allow the index time to catch up
        time.sleep(2)
        
        # create a replacement article
        z = models.Article()
        y = z.bibjson()
        y.title = "Replacement article for fulltext url"
        y.add_url("http://www.psychologie-aktuell.com/fileadmin/download/ptam/1-2014_20140324/01_Geiser.pdf", urltype="fulltext")
        
        # get the xwalk to determine if there is a duplicate
        xwalk = article.XWalk()
        d = xwalk.get_duplicate(z)
        
        assert d is not None
        assert d.bibjson().title == "Example 2 article with a fulltext url"
    
    def test_05(self):
        # make ourselves a couple of example articles
        a = models.Article()
        b = a.bibjson()
        b.title = "Example A article with a fulltext url"
        b.add_url("http://www.sbe.deu.edu.tr/dergi/cilt15.say%C4%B12/06%20AKALIN.pdf", urltype="fulltext")
        a.save()
        
        # wait for a bit to create good separation between last_updated times
        time.sleep(2)
        
        a2 = models.Article()
        b2 = a2.bibjson()
        b2.title = "Example B article with a fulltext url"
        b2.add_url("http://www.sbe.deu.edu.tr/dergi/cilt15.say%C4%B12/06%20AKALIN.pdf", urltype="fulltext")
        a2.save()

        # wait for a bit to create good separation between last_updated times
        time.sleep(2)

        # create an article which should not be caught by the duplicate detection
        not_duplicate = models.Article()
        not_duplicate_bibjson = not_duplicate.bibjson()
        not_duplicate_bibjson.title = "Example C article with a fulltext url"
        not_duplicate_bibjson.add_url("http://www.sbe.deu.edu.tr/dergi/cilt15.say%C4%B12/06%20AKALIN.pdf_DIFFERENT", urltype="fulltext")
        not_duplicate.save()
        
        # pause to allow the index time to catch up
        time.sleep(2)
        
        # create a replacement article
        z = models.Article()
        y = z.bibjson()
        y.title = "Replacement article for fulltext url"
        y.add_url("http://www.sbe.deu.edu.tr/dergi/cilt15.say%C4%B12/06%20AKALIN.pdf", urltype="fulltext")
        
        # get the xwalk to determine if there is a duplicate
        xwalk = article.XWalk()
        d = xwalk.get_duplicate(z)
        
        assert d is not None
        assert d.bibjson().title == "Example B article with a fulltext url", d.bibjson().title

        # get the xwalk to determine all duplicates
        # sort both results and expectations here to avoid false alarm
        # we don't care about the order of duplicates
        expected = sorted([a, a2])
        xwalk = article.XWalk()
        l = xwalk.get_duplicate(z, all_duplicates=True)
        assert isinstance(l, list), l
        assert l
        l.sort()
        assert expected == l

    def test_05_with_doi_instead(self):
        # make ourselves a couple of example articles
        a = models.Article()
        b = a.bibjson()
        b.title = "Example A article with a fulltext url"
        b.add_identifier('doi', "10.doi")
        a.save()

        # wait for a bit to create good separation between last_updated times
        time.sleep(2)

        a2 = models.Article()
        b2 = a2.bibjson()
        b2.title = "Example B article with a fulltext url"
        b2.add_identifier('doi', "10.doi")
        a2.save()

        # wait for a bit to create good separation between last_updated times
        time.sleep(2)

        # create an article which should not be caught by the duplicate detection
        not_duplicate = models.Article()
        not_duplicate_bibjson = not_duplicate.bibjson()
        not_duplicate_bibjson.title = "Example C article with a fulltext url"
        not_duplicate_bibjson.add_identifier('doi', "10.doi.DIFFERENT")
        not_duplicate.save()

        # pause to allow the index time to catch up
        time.sleep(2)

        # create a replacement article
        z = models.Article()
        y = z.bibjson()
        y.title = "Replacement article for fulltext url"
        y.add_identifier('doi', "10.doi")

        # get the xwalk to determine if there is a duplicate
        xwalk = article.XWalk()
        d = xwalk.get_duplicate(z)

        assert d is not None
        assert d.bibjson().title == "Example B article with a fulltext url", d.bibjson().title

        # get the xwalk to determine all duplicates
        # sort both results and expectations here to avoid false alarm
        # we don't care about the order of duplicates
        expected = sorted([a, a2])
        xwalk = article.XWalk()
        l = xwalk.get_duplicate(z, all_duplicates=True)
        assert isinstance(l, list)
        assert l
        assert len(l) == 2
        l.sort()
        assert expected == l
    
    def test_06(self):
        id1 = uuid.uuid4().hex
        id2 = uuid.uuid4().hex

        a = models.Article()
        a.set_id(id1)
        b = a.bibjson()
        b.title = "Example A article with a fulltext url"
        b.abstract = "a bunch of text"
        b.add_url("http://www.sbe.deu.edu.tr/dergi/cilt15.say%C4%B12/06%20AKALIN.pdf", urltype="fulltext")


        a2 = models.Article()
        a2.set_id(id2)
        b2 = a2.bibjson()
        b2.title = "Example B article with a fulltext url"
        b2.add_url("http://www.sbe.deu.edu.tr/dergi/cilt15.say%C4%B12/06%20AKALIN.pdf", urltype="fulltext")
        
        assert a2.id == id2
        
        a2.merge(a)
        
        assert a2.id == id1, (a2.id, id1, id2)
        assert a2.bibjson().title == "Example B article with a fulltext url"
        assert a2.bibjson().abstract is None
    
    def test_07(self):
        a = models.Article()
        id_ = uuid.uuid4().hex
        a.set_id(id_)
        b = a.bibjson()
        b.title = "Example A article with a fulltext url"
        b.abstract = "a bunch of text"
        b.add_url("http://www.sbe.deu.edu.tr/dergi/cilt15.say%C4%B12/06%20AKALIN.pdf", urltype="fulltext")
        
        a2 = models.Article()
        b2 = a2.bibjson()
        b2.title = "Example B article with a fulltext url"
        b2.add_url("http://www.sbe.deu.edu.tr/dergi/cilt15.say%C4%B12/06%20AKALIN.pdf", urltype="fulltext")
        
        a2.merge(a)
        
        assert a2.id == id_, (a2.id, id_)
        assert a2.bibjson().title == "Example B article with a fulltext url"
        assert a2.bibjson().abstract is None
        
    def test_08(self):
        # make ourselves a couple of example articles
        a = models.Article()
        b = a.bibjson()
        b.title = "Example A article with a fulltext url"
        b.add_url("http://www.sbe.deu.edu.tr/dergi/cilt15.say%C4%B12/06%20AKALIN.pdf", urltype="fulltext")
        a.save()

        # create an article which should not be caught by the duplicate detection
        not_duplicate = models.Article()
        not_duplicate_bibjson = not_duplicate.bibjson()
        not_duplicate_bibjson.title = "Example C article with a fulltext url"
        not_duplicate_bibjson.add_url("http://www.sbe.deu.edu.tr/dergi/cilt15.say%C4%B12/06%20AKALIN.pdf_DIFFERENT", urltype="fulltext")
        not_duplicate.save()

        # pause to allow the index time to catch up
        time.sleep(2)

        # get the xwalk to determine if there is a duplicate
        xwalk = article.XWalk()
        d = xwalk.get_duplicate(a)

        # TODO: This is complete nonsense, we must refactor get_duplicate
        # so it doesn't return the article that is being passed in when
        # requesting a single duplicate!
        # This may have implications for XML upload ingestion and could be non-trivial.
        # If you request multiple duplicates with all_duplicates=True it
        # will act intuitively and not return the article you asked for.
        assert d is not None  # current behaviour, but should be changed!
        assert d.id == a.id  # current behaviour, but should be changed!

        # get the xwalk to determine all duplicates - they do not include
        # the original
        xwalk = article.XWalk()
        l = xwalk.get_duplicate(a, all_duplicates=True)
        assert isinstance(l, list)
        assert l == []

    def test_09_many_issns(self):
        # This tests that a query with a LOT of issns is still successful
        a = models.Article()
        b = a.bibjson()
        b.journal_issns = ["0000-0000"]
        b.title = "Example A article with a fulltext url"
        b.add_identifier(b.DOI, "10.1234/duplicate")
        a.save()

        time.sleep(2)

        def random_issn():
            bits = []
            for i in range(8):
                bits.append(str(randint(1, 9)))
            return "".join(bits[:4]) + "-" + "".join(bits[4:])

        issns = [random_issn() for i in range(2000)] + ["0000-0000"]

        dupes = models.Article.duplicates(issns=issns, doi="10.1234/duplicate")
        assert len(dupes) == 1
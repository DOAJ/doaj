from unittest import TestCase
from portality import article, models
import uuid, time

id = uuid.uuid4().hex
id2 = uuid.uuid4().hex

class TestArticleMatch(TestCase):

    def setUp(self):
        pass

    def tearDown(self):    
        models.Article.remove_by_id(id)
        models.Article.remove_by_id(id2)
        # pass

    def test_01(self):
        # make ourselves an example article
        a = models.Article()
        a.set_id(id)
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
        a.set_id(id)
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
        a.set_id(id)
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
        a.set_id(id)
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
        a.set_id(id)
        b = a.bibjson()
        b.title = "Example A article with a fulltext url"
        b.add_url("http://www.sbe.deu.edu.tr/dergi/cilt15.say%C4%B12/06%20AKALIN.pdf", urltype="fulltext")
        a.save()
        
        # wait for a bit to create good separation between last_updated times
        time.sleep(2)
        
        a2 = models.Article()
        a2.set_id(id2)
        b2 = a2.bibjson()
        b2.title = "Example B article with a fulltext url"
        b2.add_url("http://www.sbe.deu.edu.tr/dergi/cilt15.say%C4%B12/06%20AKALIN.pdf", urltype="fulltext")
        a2.save()
        
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
    
    def test_06(self):
        a = models.Article()
        a.set_id(id)
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
        
        assert a2.id == id, (a2.id, id, id2)
        assert a2.bibjson().title == "Example B article with a fulltext url"
        assert a2.bibjson().abstract is None
    
    def test_07(self):
        a = models.Article()
        a.set_id(id)
        b = a.bibjson()
        b.title = "Example A article with a fulltext url"
        b.abstract = "a bunch of text"
        b.add_url("http://www.sbe.deu.edu.tr/dergi/cilt15.say%C4%B12/06%20AKALIN.pdf", urltype="fulltext")
        
        a2 = models.Article()
        b2 = a2.bibjson()
        b2.title = "Example B article with a fulltext url"
        b2.add_url("http://www.sbe.deu.edu.tr/dergi/cilt15.say%C4%B12/06%20AKALIN.pdf", urltype="fulltext")
        
        a2.merge(a)
        
        assert a2.id == id, (a2.id, id, id2)
        assert a2.bibjson().title == "Example B article with a fulltext url"
        assert a2.bibjson().abstract is None
        

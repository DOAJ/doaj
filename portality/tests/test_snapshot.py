from unittest import TestCase
from portality import models
import uuid, time

id = uuid.uuid4().hex
id2 = uuid.uuid4().hex
hid = None

class TestSnapshot(TestCase):

    def setUp(self):
        hid = None

    def tearDown(self):    
        models.Article.remove_by_id(id)
        models.Article.remove_by_id(id2)
        if hid is not None:
            models.ArticleHistory.remove_by_id(hid)

    def test_01_snapshot(self):
        # make ourselves an example article
        a = models.Article()
        a.set_id(id)
        b = a.bibjson()
        b.title = "Example article with a fulltext url"
        b.add_url("http://examplejournal.telfor.rs/Published/Vol1No1/Vol1No1_A5.pdf", urltype="fulltext")
        a.save()
        
        # snapshot it
        a.snapshot()
        
        # let the index catch up, then we can check this worked
        time.sleep(2)
        
        hist = models.ArticleHistory.get_history_for(id)
        if hist is not None:
            hid = hist[0].data.get("id")
        assert len(hist) == 1
        assert hist[0].data.get("bibjson", {}).get("title") == "Example article with a fulltext url"
    
    def test_02_merge(self):
        # make ourselves an example article
        a = models.Article()
        a.set_id(id)
        b = a.bibjson()
        b.title = "Example 2 article with a fulltext url"
        b.add_url("http://examplejournal.telfor.rs/Published/Vol1No1/Vol1No1_A5.pdf", urltype="fulltext")
        a.save()
        
        # create a replacement article
        z = models.Article()
        z.set_id(id2)
        y = z.bibjson()
        y.title = "Replacement article for fulltext url"
        y.add_url("http://examplejournal.telfor.rs/Published/Vol1No1/Vol1No1_A5.pdf", urltype="fulltext")
        
        # do a merge
        z.merge(a)
        
        # let the index catch up, then we can check this worked
        time.sleep(2)
        
        hist = models.ArticleHistory.get_history_for(id)
        if hist is not None:
            hid = hist[0].data.get("id")
        assert len(hist) == 1
        assert hist[0].data.get("bibjson", {}).get("title") == "Example 2 article with a fulltext url"
        

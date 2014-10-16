from doajtest.helpers import DoajTestCase
from portality import models
import time

class TestSnapshot(DoajTestCase):

    def setUp(self):
        super(TestSnapshot, self).setUp()

    def tearDown(self):    
        super(TestSnapshot, self).tearDown()

    def test_01_snapshot(self):
        # make ourselves an example article
        a = models.Article()
        b = a.bibjson()
        b.title = "Example article with a fulltext url"
        b.add_url("http://examplejournal.telfor.rs/Published/Vol1No1/Vol1No1_A5.pdf", urltype="fulltext")
        a.save()
        
        # snapshot it
        a.snapshot()
        
        # let the index catch up, then we can check this worked
        time.sleep(2)
        
        hist = models.ArticleHistory.get_history_for(a.id)
        assert len(hist) == 1
        assert hist[0].data.get("bibjson", {}).get("title") == "Example article with a fulltext url"
    
    def test_02_merge(self):
        # make ourselves an example article
        a = models.Article()
        b = a.bibjson()
        b.title = "Example 2 article with a fulltext url"
        b.add_url("http://examplejournal.telfor.rs/Published/Vol1No1/Vol1No1_A5.pdf", urltype="fulltext")
        a.save()
        
        # create a replacement article
        z = models.Article()
        y = z.bibjson()
        y.title = "Replacement article for fulltext url"
        y.add_url("http://examplejournal.telfor.rs/Published/Vol1No1/Vol1No1_A5.pdf", urltype="fulltext")
        
        # do a merge
        z.merge(a)
        
        # let the index catch up, then we can check this worked
        time.sleep(2)
        
        hist = models.ArticleHistory.get_history_for(a.id)
        print hist
        print len(hist)
        assert len(hist) == 1
        assert hist[0].data.get("bibjson", {}).get("title") == "Example 2 article with a fulltext url"

    def test_03_snapshot_journal(self):
        # make ourselves an example journal
        j = models.Journal()
        b = j.bibjson()
        b.title = "Example journal"
        b.add_url("http://examplejournal.telfor.rs")

        # the snapshot is part of the save method
        j.save()

        # let the index catch up, then we can check this worked
        time.sleep(5)

        hist = models.JournalHistory.get_history_for(j.id)
        assert len(hist) == 1
        assert hist[0].data.get("bibjson", {}).get("title") == "Example journal"

        

from doajtest.helpers import DoajTestCase
from portality import models
import time
import json

class TestSnapshot(DoajTestCase):

    def setUp(self):
        super(TestSnapshot, self).setUp()

    def tearDown(self):    
        super(TestSnapshot, self).tearDown()
        # snapshotting creates files in the history folder, but these
        # are cleaned up in the parent DoajTestCase class so they
        # don't have to be cleaned up in each test suite that causes .snapshot()

    def test_01_snapshot(self):
        # make ourselves an example article
        a = models.Article()
        b = a.bibjson()
        b.title = "Example article with a fulltext url"
        b.add_url("http://examplejournal.telfor.rs/Published/Vol1No1/Vol1No1_A5.pdf", urltype="fulltext")
        a.save()
        
        # snapshot it
        a.snapshot()

        assert len(self.list_today_article_history_files()) == 1
        with open(self.list_today_article_history_files()[0], 'r', encoding="utf-8") as i:
            hist = json.loads(i.read())
        assert hist
        assert hist.get("bibjson", {}).get("title") == "Example article with a fulltext url"
    
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
        
        history_files = self.list_today_article_history_files()
        assert len(history_files) == 1

        with open(history_files[0], 'r', encoding="utf-8") as i:
            hist = json.loads(i.read())
        assert hist
        assert hist.get("bibjson", {}).get("title") == "Example 2 article with a fulltext url"

    def test_03_snapshot_journal(self):
        # make ourselves an example journal
        j = models.Journal()
        b = j.bibjson()
        b.title = "Example journal"

        # the snapshot is part of the save method
        j.save(blocking=True)

        history_files = self.list_today_journal_history_files()
        assert len(history_files) == 1
        with open(history_files[0], 'r', encoding="utf-8") as i:
            hist = json.loads(i.read())
        assert hist.get("bibjson", {}).get("title") == "Example journal"
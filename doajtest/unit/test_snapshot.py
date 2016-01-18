from doajtest.helpers import DoajTestCase
from portality import models
from portality.core import app
from datetime import datetime
import time
import os
import json
from glob import glob

class TestSnapshot(DoajTestCase):

    def setUp(self):
        super(TestSnapshot, self).setUp()
        self.paths_to_delete = []

    def tearDown(self):    
        super(TestSnapshot, self).tearDown()
        for f in self.paths_to_delete:
            os.remove(f)

    def test_01_snapshot(self):
        # make ourselves an example article
        a = models.Article()
        b = a.bibjson()
        b.title = "Example article with a fulltext url"
        b.add_url("http://examplejournal.telfor.rs/Published/Vol1No1/Vol1No1_A5.pdf", urltype="fulltext")
        a.save()
        
        # snapshot it
        history_record_id = a.snapshot()
        history_record_path = os.path.join(app.config['ARTICLE_HISTORY_DIR'], datetime.now().strftime('%Y-%m-%d'), '{0}.json'.format(history_record_id))

        with open(history_record_path, 'rb') as i:
            hist = json.loads(i.read())
        assert hist
        assert hist.get("bibjson", {}).get("title") == "Example article with a fulltext url"
        self.paths_to_delete.append(history_record_path)
    
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
        
        history_files = glob(os.path.join(app.config['ARTICLE_HISTORY_DIR'], datetime.now().strftime('%Y-%m-%d'), '*'))
        assert len(history_files) == 1

        with open(history_files[0], 'rb') as i:
            hist = json.loads(i.read())
        assert hist
        assert hist.get("bibjson", {}).get("title") == "Example 2 article with a fulltext url"
        self.paths_to_delete.append(history_files[0])

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

        

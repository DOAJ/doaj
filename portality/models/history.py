from portality.core import app
from portality.dao import DomainObject
from datetime import datetime
import os
import json

class ArticleHistory(DomainObject):
    __type__ = "article_history"

    def save(self):  # method signature intentionally kept different from base class to indicate you can't do the usual things on .save()
        """
        Override usual DomainObject.save method so instead of sending
        to Elasticsearch, this will save objects in files on a daily
        directory basis. A new history object should be created every time
        when a new snapshot of an article or journal is needed - i.e.
        they are never changed and re-saved.

        With this implementation if a history object is changed and saved
        a 2nd time (after the initial save to put it on disk):
          - the file will be overwritten (if it saved 2+ times on the same
           day)
          OR
          - a new file will be created in a new directory (if the 2nd+ time
           it's saved is on a different day).
        """
        self.set_id(self.makeid())
        directory_name = datetime.now().strftime('%Y-%m-%d')
        full_dir = os.path.join(app.config['ARTICLE_HISTORY_DIR'], directory_name)
        full_path = os.path.join(full_dir, "{0}.json".format(self.id))

        if not os.path.isdir(full_dir):
            os.makedirs(full_dir)

        with open(full_path, 'wb') as o:
            o.write(json.dumps(self.data, indent=4))

class ArticleHistoryQuery(object):
    def __init__(self, about):
        self.about = about
    def query(self):
        q = {
            "query" : {
                "bool" : {
                    "must" : [
                        {"term" : {"about.exact" : self.about}}
                    ]
                }
            },
            "sort" : [{"created_date" : {"order" : "desc"}}]
        }
        return q

class JournalHistory(DomainObject):
    __type__ = "journal_history"

    @classmethod
    def get_history_for(cls, about):
        q = JournalHistoryQuery(about)
        res = cls.query(q=q.query())
        hists = [cls(**hit.get("_source")) for hit in res.get("hits", {}).get("hits", [])]
        return hists

class JournalHistoryQuery(object):
    def __init__(self, about):
        self.about = about
    def query(self):
        q = {
            "query" : {
                "bool" : {
                    "must" : [
                        {"term" : {"about.exact" : self.about}}
                    ]
                }
            },
            "sort" : [{"created_date" : {"order" : "desc"}}]
        }
        return q
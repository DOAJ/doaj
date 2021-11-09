from portality.dao import DomainObject as DomainObject
from copy import deepcopy
from datetime import datetime


class News(DomainObject):
    """~~News:Model~~"""
    __type__ = "news"

    @classmethod
    def by_remote_id(cls, remote_id):
        # ~~->News:Query~~
        q = NewsQuery(remote_id)
        es_result = cls.query(q=q.query())
        records = [News(**r.get("_source")) for r in es_result.get("hits", {}).get("hits", [])]
        return records

    @classmethod
    def latest(cls, n):
        q = NewsQuery(size=n)
        es_result = cls.query(q=q.query())
        records = [News(**r.get("_source")) for r in es_result.get("hits", {}).get("hits", [])]
        return records

    @property
    def remote_id(self): return self.data.get("remote_id")
    @remote_id.setter
    def remote_id(self, rid): self.data["remote_id"] = rid

    @property
    def url(self): return self.data.get("url")
    @url.setter
    def url(self, link): self.data["url"] = link

    @property
    def title(self): return self.data.get("title")
    @title.setter
    def title(self, t): self.data["title"] = t

    @property
    def updated(self): return self.data.get("updated")
    @updated.setter
    def updated(self, date): self.data["updated"] = date

    @property
    def published(self): return self.data.get("published")
    @published.setter
    def published(self, date): self.data["published"] = date

    @property
    def summary(self): return self.data.get("summary")
    @summary.setter
    def summary(self, s): self.data["summary"] = s

    def published_formatted(self, format="%-d %B %Y"):
        try:
            dt = datetime.strptime(self.published, "%Y-%m-%dT%H:%M:%SZ")
            return dt.strftime(format)
        except:
            return self.published


class NewsQuery(object):
    """~~News:Query->Elasticsearch:Technology~~"""
    _remote_term =  { "term" : { "remote_id.exact" : "<remote id>" } }

    def __init__(self, remote_id=None, size=5):
        self.remote_id = remote_id
        self.size = size

    def query(self):
        q = {"query" : {}, "size" : self.size, "sort" : {"published" : {"order" : "desc"}}}
        if self.remote_id is not None:
            rt = deepcopy(self._remote_term)
            rt["term"]["remote_id.exact"] = self.remote_id
            q["query"].update(rt)
        else:
            q["query"]["match_all"] = {}
        return q

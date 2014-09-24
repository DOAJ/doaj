from portality.dao import DomainObject

class ArticleHistory(DomainObject):
    __type__ = "article_history"

    @classmethod
    def get_history_for(cls, about):
        q = ArticleHistoryQuery(about)
        res = cls.query(q=q.query())
        hists = [cls(**hit.get("_source")) for hit in res.get("hits", {}).get("hits", [])]
        return hists

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
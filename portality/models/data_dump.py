from portality.lib.seamless import SeamlessMixin
from portality.dao import DomainObject
from portality.lib.coerce import COERCE_MAP
from datetime import datetime
from portality.lib import dates
from typing import Union


DATA_DUMP_STRUCT = {
    "fields" : {
        "id" : {"coerce" : "unicode"},
        "created_date" : {"coerce" : "utcdatetime"},
        "last_updated" : {"coerce" : "utcdatetime"},
        "es_type": {"coerce": "unicode"},
        "dump_date": {"coerce": "utcdatetime"},
    },
    "objects": [
        "article",
        "journal"
    ],
    "structs": {
        "article": {
            "fields": {
                "container": {"coerce": "unicode"},
                "filename": {"coerce": "unicode"},
                "url": {"coerce": "unicode"},
                "size": {"coerce": "integer"}
            }
        },
        "journal": {
            "fields": {
                "container": {"coerce": "unicode"},
                "filename": {"coerce": "unicode"},
                "url": {"coerce": "unicode"},
                "size": {"coerce": "integer"}
            }
        }
    }
}


class DataDump(SeamlessMixin, DomainObject):
    __type__ = "data_dump"

    __SEAMLESS_STRUCT__ = DATA_DUMP_STRUCT
    __SEAMLESS_COERCE__ = COERCE_MAP

    @classmethod
    def all_dumps_before(cls, cutoff: datetime) -> list:
        q = CutoffQuery(cutoff)
        return cls.object_query(q.query())

    @classmethod
    def find_by_filename(cls, filename: str) -> 'DataDump':
        q = FilenameQuery(filename)
        return cls.object_query(q.query())

    @classmethod
    def find_latest(cls):
        q = LatestQuery()
        res = cls.object_query(q.query())
        if res is not None and len(res) > 0:
            return res[0]
        return None

    @classmethod
    def first_dump_after(cls, cutoff: datetime) -> Union[None, 'DataDump']:
        q = FirstAfterQuery(cutoff)
        res = cls.object_query(q.query())
        if res is not None and len(res) > 0:
            return res[0]
        return None

    @property
    def dump_date(self):
        return self.__seamless__.get_single("dump_date", coerce=COERCE_MAP["datetime"])

    @dump_date.setter
    def dump_date(self, dump_date: Union[str, datetime]):
        self.__seamless__.set_with_struct("dump_date", dump_date)

    def set_article_dump(self, container, filename, size, url):
        self.__seamless__.set_with_struct("article", {
            "container": container,
            "filename": filename,
            "url": url,
            "size": size
        })

    @property
    def article_container(self):
        return self.__seamless__.get_single("article.container")

    @property
    def article_filename(self):
        return self.__seamless__.get_single("article.filename")

    def set_journal_dump(self, container, filename, size, url):
        self.__seamless__.set_with_struct("journal", {
            "container": container,
            "filename": filename,
            "url": url,
            "size": size
        })

    @property
    def joural_container(self):
        return self.__seamless__.get_single("journal.container")

    @property
    def journal_filename(self):
        return self.__seamless__.get_single("journal.filename")


class CutoffQuery(object):
    def __init__(self, cutoff: datetime):
        self.cutoff = cutoff

    def query(self):
        return {
            "query": {
                "range": {
                    "dump_date": {
                        "lt": dates.format(self.cutoff)
                    }
                }
            }
        }

class FirstAfterQuery(object):
    def __init__(self, cutoff: datetime):
        self.cutoff = cutoff

    def query(self):
        return {
            "query": {
                "range": {
                    "dump_date": {
                        "gte": dates.format(self.cutoff)
                    }
                }
            },
            "sort": {
                "dump_date": {
                    "order": "asc"
                }
            },
            "size": 1
        }

class LatestQuery:
    def query(self):
        return {
            "query": {
                "match_all": {}
            },
            "sort": {
                "dump_date": {
                    "order": "desc"
                }
            },
            "size": 1
        }

class FilenameQuery(object):
    def __init__(self, filename: str):
        self.filename = filename

    def query(self):
        return {
            "query": {
                "bool": {
                    "should": [
                        {
                            "term": {
                                "article.filename": self.filename
                            }
                        },
                        {
                            "term": {
                                "journal.filename": self.filename
                            }
                        }
                    ]
                }
            }
        }
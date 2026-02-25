from portality.lib.seamless import SeamlessMixin
from portality.dao import DomainObject
from portality.lib.coerce import COERCE_MAP
from datetime import datetime
from portality.lib import dates, es_data_mapping
from typing import Union, List
from portality.core import app


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

MAPPING_OPTS = {
    "dynamic": None,
    "coerces": app.config["DATAOBJ_TO_MAPPING_DEFAULTS"]
}

class DataDump(SeamlessMixin, DomainObject):
    __type__ = "data_dump"

    __SEAMLESS_STRUCT__ = DATA_DUMP_STRUCT
    __SEAMLESS_COERCE__ = COERCE_MAP

    def __init__(self, **kwargs):
        # FIXME: hack, to deal with ES integration layer being improperly abstracted
        if "_source" in kwargs:
            kwargs = kwargs["_source"]
        super(DataDump, self).__init__(raw=kwargs)

    def mappings(self):
        return es_data_mapping.create_mapping(self.__seamless_struct__.raw, MAPPING_OPTS)

    @property
    def data(self):
        return self.__seamless__.data

    @classmethod
    def all_dumps_before(cls, cutoff: datetime) -> list:
        q = CutoffQuery(cutoff)
        return cls.object_query(q.query())

    @classmethod
    def find_by_filename(cls, filename: str) -> List['DataDump']:
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

    def remove_article_dump(self):
        self.__seamless__.delete("article")

    @property
    def article_container(self):
        return self.__seamless__.get_single("article.container")

    @property
    def article_filename(self):
        return self.__seamless__.get_single("article.filename")

    @property
    def article_url(self):
        return self.__seamless__.get_single("article.url")

    @property
    def article_size(self):
        return self.__seamless__.get_single("article.size")

    @property
    def article_size_human(self):
        value = self.article_size
        if value is not None:
            return self._int_to_filesize(value)
        return None

    def set_journal_dump(self, container, filename, size, url):
        self.__seamless__.set_with_struct("journal", {
            "container": container,
            "filename": filename,
            "url": url,
            "size": size
        })

    def remove_journal_dump(self):
        self.__seamless__.delete("journal")

    @property
    def journal_container(self):
        return self.__seamless__.get_single("journal.container")

    @property
    def journal_filename(self):
        return self.__seamless__.get_single("journal.filename")

    @property
    def journal_size(self):
        return self.__seamless__.get_single("journal.size")

    @property
    def journal_size_human(self):
        value = self.article_size
        if value is not None:
            return self._int_to_filesize(value)
        return None

    @property
    def journal_url(self):
        return self.__seamless__.get_single("journal.url")

    def _int_to_filesize(self, value):
        if value is not None:
            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                if value < 1024.0:
                    return f"{value:.2f} {unit}"
                value /= 1024.0
            return f"{value:.2f} PB"
        return None

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
            },
            "sort": {
                "dump_date": {
                    "order": "asc"  # oldest first
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
                                "article.filename.exact": self.filename
                            }
                        },
                        {
                            "term": {
                                "journal.filename.exact": self.filename
                            }
                        }
                    ]
                }
            }
        }
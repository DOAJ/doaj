from portality.lib.seamless import SeamlessMixin
from portality.dao import DomainObject
from portality.lib.coerce import COERCE_MAP
from datetime import datetime
from portality.lib import dates, es_data_mapping
from typing import Union, List
from portality.core import app


JOURNAL_CSV_STRUCT = {
    "fields" : {
        "id" : {"coerce" : "unicode"},
        "created_date" : {"coerce" : "utcdatetime"},
        "last_updated" : {"coerce" : "utcdatetime"},
        "es_type": {"coerce": "unicode"},
        "export_date": {"coerce": "utcdatetime"},
        "container": {"coerce": "unicode"},
        "filename": {"coerce": "unicode"},
        "url": {"coerce": "unicode"},
        "size": {"coerce": "integer"}
    }
}

MAPPING_OPTS = {
    "dynamic": None,
    "coerces": app.config["DATAOBJ_TO_MAPPING_DEFAULTS"]
}

class JournalCSV(SeamlessMixin, DomainObject):
    __type__ = "journal_csv"

    __SEAMLESS_STRUCT__ = JOURNAL_CSV_STRUCT
    __SEAMLESS_COERCE__ = COERCE_MAP

    def __init__(self, **kwargs):
        # FIXME: hack, to deal with ES integration layer being improperly abstracted
        if "_source" in kwargs:
            kwargs = kwargs["_source"]
        super(JournalCSV, self).__init__(raw=kwargs)

    def mappings(self):
        return es_data_mapping.create_mapping(self.__seamless_struct__.raw, MAPPING_OPTS)

    @property
    def data(self):
        return self.__seamless__.data

    @classmethod
    def all_csvs_before(cls, cutoff: datetime) -> list:
        q = CutoffQuery(cutoff)
        return cls.object_query(q.query())

    @classmethod
    def find_by_filename(cls, filename: str) -> List['JournalCSV']:
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
    def first_csv_after(cls, cutoff: datetime) -> Union[None, 'JournalCSV']:
        q = FirstAfterQuery(cutoff)
        res = cls.object_query(q.query())
        if res is not None and len(res) > 0:
            return res[0]
        return None

    @property
    def export_date(self):
        return self.__seamless__.get_single("export_date", coerce=COERCE_MAP["datetime"])

    @property
    def export_day(self):
        return self.__seamless__.get_single("export_date", coerce=COERCE_MAP["bigenddate"])

    @export_date.setter
    def export_date(self, dump_date: Union[str, datetime]):
        self.__seamless__.set_with_struct("export_date", dump_date)

    def set_csv(self, container, filename, size, url):
        self.__seamless__.set_with_struct("container", container)
        self.__seamless__.set_with_struct("filename", filename)
        self.__seamless__.set_with_struct("url", url)
        self.__seamless__.set_with_struct("size", size)

    @property
    def container(self):
        return self.__seamless__.get_single("container")

    @property
    def filename(self):
        return self.__seamless__.get_single("filename")

    @property
    def url(self):
        return self.__seamless__.get_single("url")


class CutoffQuery(object):
    def __init__(self, cutoff: datetime):
        self.cutoff = cutoff

    def query(self):
        return {
            "query": {
                "range": {
                    "export_date": {
                        "lt": dates.format(self.cutoff)
                    }
                }
            },
            "sort": {
                "export_date": {
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
                    "export_date": {
                        "gte": dates.format(self.cutoff)
                    }
                }
            },
            "sort": {
                "export_date": {
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
                "export_date": {
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
                    "must": [
                        {
                            "term": {
                                "filename.exact": self.filename
                            }
                        }
                    ]
                }
            }
        }
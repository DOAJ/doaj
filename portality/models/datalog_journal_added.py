from __future__ import annotations

import elasticsearch

from portality import dao
from portality.dao import DomainObject, ScrollInitialiseException
from portality.lib import coerce
from portality.lib.coerce import COERCE_MAP
from portality.lib.seamless import SeamlessMixin


class DatalogJournalAdded(SeamlessMixin, DomainObject):
    __type__ = "datalog_journal_added"
    DATE_FMT = '%d-%B-%Y'

    __SEAMLESS_STRUCT__ = {
        "fields": {
            "id": {"coerce": "unicode"},
            "title": {"coerce": "unicode"},
            "issn": {"coerce": "unicode"},
            "date_added": {"coerce": "utcdatetime-datalog"},
            "has_continuations": {"coerce": "bool"},
            "journal_id": {"coerce": "unicode"},
            "created_date": {"coerce": "utcdatetime"},
            "last_updated": {"coerce": "utcdatetime"},
            'es_type': {'coerce': 'unicode'},
        },
    }

    __SEAMLESS_COERCE__ = {
        **COERCE_MAP,
        "utcdatetime-datalog": coerce.date_str(in_format=DATE_FMT),
    }

    def __init__(self, **kwargs):
        super(DatalogJournalAdded, self).__init__(raw=kwargs)

    @property
    def data(self):
        return self.__seamless__.data

    @property
    def title(self):
        return self.__seamless__.get_single('title')

    @title.setter
    def title(self, val):
        self.__seamless__.set_single('title', val)

    @property
    def issn(self):
        return self.__seamless__.get_single("issn")

    @issn.setter
    def issn(self, val):
        self.__seamless__.set_single('issn', val)

    @property
    def date_added(self):
        return self.__seamless__.get_single("date_added")

    @date_added.setter
    def date_added(self, val):
        self.__seamless__.set_with_struct('date_added', val)

    @property
    def date_added_str(self):
        return self.date_added.strftime(self.DATE_FMT)

    @property
    def has_continuations(self):
        return self.__seamless__.get_single("has_continuations")

    @has_continuations.setter
    def has_continuations(self, val):
        self.__seamless__.set_single('has_continuations', val)

    @property
    def journal_id(self):
        return self.__seamless__.get_single("journal_id")

    @journal_id.setter
    def journal_id(self, val):
        self.__seamless__.set_single('journal_id', val)


class LastDatalogJournalAddedQuery:

    def query(self):
        return {
            "size": 1,
            "sort": [
                {
                    "date_added": {
                        "order": "desc"
                    }
                }
            ],
            "query": {
                "match_all": {}
            }
        }


def find_last_datalog():
    try:
        record = next(DatalogJournalAdded.iterate(LastDatalogJournalAddedQuery().query()), None)
    except (elasticsearch.exceptions.NotFoundError, ScrollInitialiseException):
        record = None
    return record


class DateAddedDescQuery:

    def query(self):
        return {
            'sort': [
                {'date_added': {'order': 'desc'}}
            ]
        }


class IssnDateMatchQuery:
    def __init__(self, issn, date_added):
        self.issn = issn
        self.date_added = date_added

    def query(self):
        return {
            "query": {
                "bool": {
                    "filter": [
                        {"term": {"issn.keyword": self.issn}},
                        {"term": {"date_added": self.date_added}}
                    ]
                }
            },
        }


def is_issn_exists(issn, date_added):
    return dao.is_exist(IssnDateMatchQuery(issn, date_added).query(), DatalogJournalAdded.index_name())

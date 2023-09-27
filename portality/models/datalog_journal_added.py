import datetime

from portality.dao import DomainObject
from portality.lib import dates, coerce
from portality.lib.seamless import SeamlessMixin


class DatalogJournalAdded(SeamlessMixin, DomainObject):
    __type__ = "datalog_journal_added"
    DATE_FMT = '%d-%B-%Y'

    __SEAMLESS_STRUCT__ = {
        "fields": {
            "id": {"coerce": "unicode"},
            "title": {"coerce": "unicode"},
            "issn": {"coerce": "unicode"},
            "date_added": {"coerce": "datetime"},
            "has_seal": {"coerce": "bool"},
            "has_continuations": {"coerce": "bool"},
            "created_date": {"coerce": "datetime"},
            "last_updated": {"coerce": "datetime"},
            'es_type': {'coerce': 'unicode'},
        },
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
        self.__seamless__.set_single('date_added', val, coerce=coerce.date_str(in_format=self.DATE_FMT))

    @property
    def date_added_str(self):
        return self.date_added.strftime(self.DATE_FMT)

    @property
    def has_seal(self):
        return self.__seamless__.get_single("has_seal")

    @has_seal.setter
    def has_seal(self, val):
        self.__seamless__.set_single('has_seal', val)

    @property
    def has_continuations(self):
        return self.__seamless__.get_single("has_continuations")

    @has_continuations.setter
    def has_continuations(self, val):
        self.__seamless__.set_single('has_continuations', val)

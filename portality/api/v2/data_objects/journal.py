from portality import models

from portality.api.v2.data_objects.common_journal_application import OutgoingCommonJournalApplication, _SHARED_STRUCT

# we only have outgoing journals for the moment
from portality.lib.coerce import COERCE_MAP

JOURNAL_STRUCT = {
    "objects": ["bibjson", "admin"],
    "fields": {
        "id": {"coerce": "unicode"},
        "created_date": {"coerce": "utcdatetime"},
        "last_updated": {"coerce": "utcdatetime"},
        "last_manual_update": {"coerce": "utcdatetime"},
        "es_type": {"coerce": "unicode"}
    },
    "structs": {
        "admin": {
            "fields": {
                "in_doaj": {"coerce": "bool", "get__default": False},
                "ticked": {"coerce": "bool", "get__default": False},
                "seal": {"coerce": "bool", "get__default": False}
            }
        }
    }
}


class OutgoingJournal(OutgoingCommonJournalApplication):

    __SEAMLESS_COERCE__ = COERCE_MAP
    __SEAMLESS_STRUCT__ = [
        JOURNAL_STRUCT,
        _SHARED_STRUCT
    ]

    def __init__(self, raw=None, **kwargs):
        super(OutgoingJournal, self).__init__(raw, silent_prune=True, **kwargs)

    @classmethod
    def from_model(cls, jm):
        assert isinstance(jm, models.Journal)
        d = super(OutgoingJournal, cls).from_model(jm)
        return d

    @classmethod
    def from_model_by_id(cls, id_):
        j = models.Journal.pull(id_)
        return cls.from_model(j)

    @property
    def data(self):
        return self.__seamless__.data
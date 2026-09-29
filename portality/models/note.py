from portality.core import app
from portality.dao import DomainObject
from portality.lib import es_data_mapping
from portality.lib.coerce import COERCE_MAP
from portality.lib.seamless import SeamlessMixin

STRUCT = {
    "fields" : {
        "id" : {"coerce" : "unicode"},
        "note" : {"coerce" : "unicode"},
        "created_date" : {"coerce" : "utcdatetime"},
        "last_updated": {"coerce" : "utcdatetime"},
        "es_type": {"coerce": "unicode"},
        "author_id" : {"coerce" : "unicode"},  # account_id of the note's author
        "resource_type": {"coerce" : "unicode"},
        "resource_id": {"coerce" : "unicode"},
    }
}

MAPPING_OPTS = {
    "dynamic": None,
    "coerces": app.config["DATAOBJ_TO_MAPPING_DEFAULTS"]
}

class Note(SeamlessMixin, DomainObject):
    __type__ = "note"

    __SEAMLESS_STRUCT__ = STRUCT
    __SEAMLESS_COERCE__ = COERCE_MAP

    @classmethod
    def all_by_resource(cls, resource_type, resource_id):
        q = NotesByResourceQuery(resource_type, resource_id)
        return [n for n in cls.iterate_unstable(q.query())]

    def __init__(self, **kwargs):
        # FIXME: hack, to deal with ES integration layer being improperly abstracted
        if "_source" in kwargs:
            kwargs = kwargs["_source"]
        super(Note, self).__init__(raw=kwargs)

    def mappings(self):
        return es_data_mapping.create_mapping(self.__seamless_struct__.raw, MAPPING_OPTS)

    @property
    def data(self):
        return self.__seamless__.data

    @property
    def note(self):
        return self.__seamless__.get_single("note")

    @note.setter
    def note(self, val):
        self.__seamless__.set_single("note", val)

    @property
    def author_id(self):
        return self.__seamless__.get_single("author_id")

    @author_id.setter
    def author_id(self, val):
        self.__seamless__.set_single("author_id", val)

    @property
    def resource_type(self):
        return self.__seamless__.get_single("resource_type")

    @resource_type.setter
    def resource_type(self, val):
        self.__seamless__.set_single("resource_type", val)

    @property
    def resource_id(self):
        return self.__seamless__.get_single("resource_id")

    @resource_id.setter
    def resource_id(self, val):
        self.__seamless__.set_single("resource_id", val)

class NotesByResourceQuery:
    def __init__(self, resource_type, resource_id):
        self._resource_type = resource_type
        self._resource_id = resource_id

    def query(self):
        return {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"resource_type": self._resource_type}},
                        {"term": {"resource_id": self._resource_id}}
                    ]
                }
            }
        }
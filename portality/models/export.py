from portality.lib.seamless import SeamlessMixin
from portality.dao import DomainObject
from portality.lib.coerce import COERCE_MAP
from portality.lib import es_data_mapping
from portality.core import app

import json

EXPORT_STRUCT = {
    "fields" : {
        "id" : {"coerce" : "unicode"},
        "created_date" : {"coerce" : "utcdatetime"},
        "last_updated" : {"coerce" : "utcdatetime"},
        "es_type": {"coerce": "unicode"},
        "requester": {"coerce": "unicode"},
        "request_date": {"coerce": "utcdatetime"},
        "generated_date": {"coerce": "utcdatetime"},
        "name": {"coerce": "unicode"},
        "filename": {"coerce": "unicode"},
        "constraints": {"coerce": "unicode"},
    }
}

MAPPING_OPTS = {
    "dynamic": None,
    "coerces": app.config["DATAOBJ_TO_MAPPING_DEFAULTS"]
}

class Export(SeamlessMixin, DomainObject):
    __type__ = 'export'

    __SEAMLESS_STRUCT__ = [EXPORT_STRUCT]
    __SEAMLESS_COERCE__ = COERCE_MAP

    def __init__(self, **kwargs):
        # FIXME: hack, to deal with ES integration layer being improperly abstracted
        if "_source" in kwargs:
            kwargs = kwargs["_source"]
        super(Export, self).__init__(raw=kwargs)

    def mappings(self):
        return es_data_mapping.create_mapping(self.__seamless_struct__.raw, MAPPING_OPTS)

    @property
    def data(self):
        return self.__seamless__.data

    @property
    def id(self):
        return self.__seamless__.get_single("id")

    @id.setter
    def id(self, value):
        self.__seamless__.set_with_struct("id", value)

    @property
    def created_date(self):
        return self.__seamless__.get_single("created_date")

    @created_date.setter
    def created_date(self, value):
        self.__seamless__.set_with_struct("created_date", value)

    @property
    def last_updated(self):
        return self.__seamless__.get_single("last_updated")

    @last_updated.setter
    def last_updated(self, value):
        self.__seamless__.set_with_struct("last_updated", value)

    @property
    def requester(self):
        return self.__seamless__.get_single("requester")

    @requester.setter
    def requester(self, value):
        self.__seamless__.set_with_struct("requester", value)

    @property
    def request_date(self):
        return self.__seamless__.get_single("request_date")

    @request_date.setter
    def request_date(self, value):
        self.__seamless__.set_with_struct("request_date", value)

    @property
    def generated_date(self):
        return self.__seamless__.get_single("generated_date")

    @generated_date.setter
    def generated_date(self, value):
        self.__seamless__.set_with_struct("generated_date", value)

    @property
    def name(self):
        return self.__seamless__.get_single("name")

    @name.setter
    def name(self, value):
        self.__seamless__.set_with_struct("name", value)

    @property
    def filename(self):
        return self.__seamless__.get_single("filename")

    @filename.setter
    def filename(self, value):
        self.__seamless__.set_with_struct("filename", value)

    @property
    def constraints(self):
        return json.loads(self.__seamless__.get_single("constraints"))

    @constraints.setter
    def constraints(self, value):
        if not isinstance(value, str):
            value = json.dumps(value)
        self.__seamless__.set_with_struct("constraints", value)

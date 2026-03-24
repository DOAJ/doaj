from io import BytesIO

from portality.core import app
from portality.dao import DomainObject
from portality.lib import es_data_mapping
from portality.lib.coerce import COERCE_MAP
from portality.lib.ris import RisEntry
from portality.lib.seamless import SeamlessMixin
from portality.lib import dates

STRUCT = {
    "fields": {
        "id": {"coerce": "unicode"},
        "created_date": {"coerce": "utcdatetime"},
        "last_updated": {"coerce": "utcdatetime"},
        "es_type": {"coerce": "unicode"},
        "ris": {"coerce": "unicode"},
    }
}

MAPPING_OPTS = {
    "dynamic": None,
    "coerces": app.config["DATAOBJ_TO_MAPPING_DEFAULTS"]
}

class RISExport(SeamlessMixin, DomainObject):
    __type__ = "ris_export"

    __SEAMLESS_STRUCT__ = STRUCT
    __SEAMLESS_COERCE__ = COERCE_MAP

    def __init__(self, **kwargs):
        # FIXME: hack, to deal with ES integration layer being improperly abstracted
        if "_source" in kwargs:
            kwargs = kwargs["_source"]
        super(RISExport, self).__init__(raw=kwargs)

    def mappings(self):
        return es_data_mapping.create_mapping(self.__seamless_struct__.raw, MAPPING_OPTS)

    @property
    def data(self):
        return self.__seamless__.data

    @property
    def ris_raw(self):
        return self.__seamless__.get_single("ris")

    @ris_raw.setter
    def ris_raw(self, val):
        if isinstance(val, RisEntry):
            val = val.to_text()
        self.__seamless__.set_with_struct("ris", val)

    @property
    def byte_stream(self):
        raw = self.ris_raw
        raw = raw.encode('utf-8', errors='ignore')
        bs = BytesIO()
        bs.write(raw)
        bs.seek(0)
        return bs

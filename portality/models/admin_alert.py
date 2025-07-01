from portality.core import app
from portality.dao import DomainObject
from portality.lib import es_data_mapping
from portality.lib.coerce import COERCE_MAP
from portality.lib.seamless import SeamlessMixin
from portality.lib import dates
from portality.models import Account

STRUCT = {
    "fields": {
        "id": {"coerce": "unicode"},
        "created_date": {"coerce": "utcdatetime"},
        "last_updated": {"coerce": "utcdatetime"},
        "es_type": {"coerce": "unicode"},
        "message": {"coerce": "unicode"},
        "source": {"coerce": "unicode"},
        "state": {"coerce": "unicode", "allowed_values": ["new", "in_progress", "closed"]}
    },
    "lists": {
        "audit": {"contains": "object"}
    },
    "structs": {
        "audit": {
            "fields": {
                "user": {"coerce": "unicode"},
                "date": {"coerce": "utcdatetime"},
                "from_state": {"coerce": "unicode"},
                "to_state": {"coerce": "unicode"}
            }
        }
    }
}

MAPPING_OPTS = {
    "dynamic": None,
    "coerces": app.config["DATAOBJ_TO_MAPPING_DEFAULTS"]
}

class AdminAlert(SeamlessMixin, DomainObject):
    __type__ = "admin_alert"

    __SEAMLESS_STRUCT__ = STRUCT
    __SEAMLESS_COERCE__ = COERCE_MAP

    STATE_NEW = "new"
    STATE_IN_PROGRESS = "in_progress"
    STATE_CLOSED = "closed"

    def __init__(self, **kwargs):
        # FIXME: hack, to deal with ES integration layer being improperly abstracted
        if "_source" in kwargs:
            kwargs = kwargs["_source"]
        super(AdminAlert, self).__init__(raw=kwargs)

    def mappings(self):
        return es_data_mapping.create_mapping(self.__seamless_struct__.raw, MAPPING_OPTS)

    @property
    def data(self):
        return self.__seamless__.data

    @property
    def source(self):
        return self.__seamless__.get_single("source")

    @source.setter
    def source(self, val):
        self.__seamless__.set_with_struct("source", val)

    @property
    def message(self):
        return self.__seamless__.get_single("message")

    @message.setter
    def message(self, val):
        self.__seamless__.set_with_struct("message", val)

    @property
    def state(self):
        return self.__seamless__.get_single("state")

    @state.setter
    def state(self, val):
        self.__seamless__.set_with_struct("state", val)

    @property
    def audit(self):
        return self.__seamless__.get_list("audit")

    def change_state(self, new_state, user: Account, date=None):
        if new_state not in [self.STATE_NEW, self.STATE_IN_PROGRESS, self.STATE_CLOSED]:
            raise ValueError(f"Invalid state: {new_state}")
        old_state = self.state
        self.state = new_state
        audit_entry = {
            "user": user.id,
            "date": date or dates.now(),
            "from_state": old_state,
            "to_state": new_state
        }
        self.__seamless__.add_to_list_with_struct("audit", audit_entry)

        self.save()
from portality.dao import DomainObject
from portality.lib import es_data_mapping
from portality.lib.coerce import COERCE_MAP
from portality.lib.seamless import SeamlessMixin
from portality.core import app
from portality.models import Application

import json

TRIAGE_STRUCT = {
    "fields": {
        "has_minimal_review": {"coerce": "bool", "default": False},
    }
}

STRUCT = {
    "fields": {
        "id": {"coerce": "unicode"},
        "created_date": {"coerce": "utcdatetime"},
        "last_updated": {"coerce": "utcdatetime"},
        "es_type": {"coerce": "unicode"},
    },
    "objects": ["application", "state", "modules", "audit"],
    "structs": {
        "application": {
            "fields": {
                "id": {"coerce": "unicode"},
                "title": {"coerce": "unicode"},
                "original": {"coerce": "unicode"},
            }
        },
        "audit": {
            "fields": {
                "user": {"coerce": "unicode"},
                "date": {"coerce": "utcdatetime"},
                "from_state": {"coerce": "unicode"},
                "to_state": {"coerce": "unicode"}
            }
        },
        "modules": {
            "objects": ["triage", "quick_fail"],
            "structs": {
                "triage": TRIAGE_STRUCT,
                "quick_fail": {}
            }
        },
        "state": {
            "fields": {
                "module": {"coerce": "unicode"},
                "stage": {"coerce": "unicode"},
                "editor_group": {"coerce": "unicode"},
                "reviewer": {"coerce": "unicode"}
            }
        }
    }
}

MAPPING_OPTS = {
    "dynamic": None,
    "coerces": app.config["DATAOBJ_TO_MAPPING_DEFAULTS"],
    "exceptions": {
        "application.original": {
            "type": "text"
        }
    }
}

class WorkflowControl(SeamlessMixin, DomainObject):
    __type__ = "workflow_control"

    __SEAMLESS_STRUCT__ = STRUCT
    __SEAMLESS_COERCE__ = COERCE_MAP

    def __init__(self, **kwargs):
        # FIXME: hack, to deal with ES integration layer being improperly abstracted
        if "_source" in kwargs:
            kwargs = kwargs["_source"]
        super(WorkflowControl, self).__init__(raw=kwargs)

    def mappings(self):
        return es_data_mapping.create_mapping(self.__seamless_struct__.raw, MAPPING_OPTS)

    @property
    def data(self):
        return self.__seamless__.data

    ####################################
    ## state properties

    @property
    def module(self):
        return self.__seamless__.get_single("state.module")

    @module.setter
    def module(self, val):
        self.__seamless__.set_single("state.module", val)

    @property
    def stage(self):
        return self.__seamless__.get_single("state.stage")

    @stage.setter
    def stage(self, val):
        self.__seamless__.set_single("state.stage", val)

    @property
    def editor_group(self):
        return self.__seamless__.get_single("state.editor_group")

    @editor_group.setter
    def editor_group(self, val):
        self.__seamless__.set_single("state.editor_group", val)

    @property
    def reviewer(self):
        return self.__seamless__.get_single("state.reviewer")

    @reviewer.setter
    def reviewer(self, val):
        self.__seamless__.set_single("state.reviewer", val)

    @reviewer.deleter
    def reviewer(self):
        self.__seamless__.delete("state.reviewer")

    ##################################
    ## Application properties

    @property
    def application_id(self):
        return self.__seamless__.get_single("application.id")

    @application_id.setter
    def application_id(self, val):
        self.__seamless__.set_single("application.id", val)

    @property
    def application_title(self):
        return self.__seamless__.get_single("application.title")

    @application_title.setter
    def application_title(self, val):
        self.__seamless__.set_single("application.title", val)

    @property
    def original_application_raw(self):
        return self.__seamless__.get_single("application.original")

    @original_application_raw.setter
    def original_application_raw(self, val):
        self.__seamless__.set_single("application.original", val)

    @property
    def original_application_json(self):
        return json.loads(self.original_application_raw)

    @property
    def original_application(self):
        j = self.original_application_json
        return Application(**j)

    @original_application.setter
    def original_application(self, val):
        raw = json.dumps(val.data)
        self.original_application_raw = raw

    ##################################
    ## Module specifics

    @property
    def triage(self):
        t = self.__seamless__.get_single("modules.triage")
        if t is None:
            self.__seamless__.set_single("modules.triage", {})
            t = self.__seamless__.get_single("modules.triage")
        return Triage(t)

class Triage(SeamlessMixin):
    __SEAMLESS_STRUCT__ = TRIAGE_STRUCT
    __SEAMLESS_COERCE__ = COERCE_MAP

    # constructor
    def __init__(self, raw=None, **kwargs):
        super(Triage, self).__init__(raw=raw, **kwargs)

    @property
    def data(self):
        return self.__seamless__.data

    @property
    def has_minimal_review(self):
        return self.__seamless__.get_single("has_minimal_review")

    @has_minimal_review.setter
    def has_minimal_review(self, val):
        self.__seamless__.set_single("has_minimal_review", val)


##########################################


from datetime import datetime
from typing import Union

from portality.dao import DomainObject
from portality.lib import es_data_mapping, dates
from portality.lib.coerce import COERCE_MAP
from portality.lib.seamless import SeamlessMixin
from portality.core import app
from portality.models import Application, Account

import json

TRIAGE_STRUCT = {
    "fields": {
        "has_minimal_review": {"coerce": "bool"},
    }
}

STRUCT = {
    "fields": {
        "id": {"coerce": "unicode"},
        "created_date": {"coerce": "utcdatetime"},
        "last_updated": {"coerce": "utcdatetime"},
        "es_type": {"coerce": "unicode"},
    },
    "lists": {
        "audit": {"contains": "object"}
    },
    "objects": ["application", "state", "modules"],
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
                "new_state": {"coerce": "unicode"}
            },
            "objects": ["new_state"],
            "structs": {
                "new_state": {
                    "fields": {
                        "module": {"coerce": "unicode"},
                        "stage": {"coerce": "unicode"},
                        "reviewer": {"coerce": "unicode"}
                    }
                }
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

    # Generic state definition values
    ANY = "*"
    UNASSIGNED = "-"
    ASSIGNED = "+"
    META_STATES = [ANY, UNASSIGNED, ASSIGNED]

    def __init__(self, **kwargs):
        # FIXME: hack, to deal with ES integration layer being improperly abstracted
        if "_source" in kwargs:
            kwargs = kwargs["_source"]
        super(WorkflowControl, self).__init__(raw=kwargs)
        self._reviewer_object = None

    ####################################
    ## Class methods for locating WorkflowControl objects

    @classmethod
    def find_by_application(cls, app_id):
        q = WorkflowControlQuery(application_id=app_id)
        objs = cls.object_query(q.query())
        if len(objs) > 1:
            raise ValueError("Multiple WorkflowControl objects found for application id: {}".format(app_id))
        elif len(objs) == 0:
            return None
        else:
            return objs[0]

    ####################################

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
    def reviewer_id(self):
        return self.__seamless__.get_single("state.reviewer")

    @reviewer_id.setter
    def reviewer_id(self, val):
        self.__seamless__.set_single("state.reviewer", val)

    @reviewer_id.deleter
    def reviewer_id(self):
        self.__seamless__.delete("state.reviewer")

    @property
    def reviewer(self):
        rid = self.reviewer_id
        if rid is None:
            self._reviewer_object = None
            return None

        if self._reviewer_object is not None:
            if self._reviewer_object.id == rid:
                return self._reviewer_object
            else:
                self._reviewer_object = None

        self._reviewer_object = Account.pull(rid)
        return self._reviewer_object

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

    ##################################
    ## Audit

    def add_audit(self, actor:Union[str, Account], new_state:dict, date:Union[str, datetime]=None):
        if date is None:
            date = dates.now()
        if isinstance(actor, Account):
            actor = actor.id

        audit_entry = {
            "user": actor,
            "date": date,
            "new_state": new_state
        }

        self.__seamless__.add_to_list_with_struct("audit", audit_entry)

    @property
    def audit(self):
        return self.__seamless__.get_list("audit")

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

class WorkflowControlQuery:
    def __init__(self, application_id=None):
        self._application_id = application_id

    def query(self):
        return {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"application.id.exact": self._application_id}}
                    ]
                }
            }
        }

class WorkflowControlStateQuery:
    def __init__(self,
                 module:str=None,
                 stage:str=None,
                 reviewer:str=None,
                 size:int=100):
        self._module = module
        self._stage = stage
        self._reviewer = reviewer
        self._size = size

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, size:int):
        self._size = size

    def query(self):
        must = []
        must_not = []

        if self._module is not None:
            if self._module != WorkflowControl.ANY:
                if self._module == WorkflowControl.UNASSIGNED:
                    must_not.append({"exists": {"field": "state.module"}})
                elif self._module == WorkflowControl.ASSIGNED:
                    must.append({"exists": {"field": "state.module"}})
                else:
                    must.append({"term": {"state.module.exact": self._module}})

        if self._stage is not None:
            if self._stage != WorkflowControl.ANY:
                if self._stage == WorkflowControl.UNASSIGNED:
                    must_not.append({"exists": {"field": "state.stage"}})
                elif self._stage == WorkflowControl.ASSIGNED:
                    must.append({"exists": {"field": "state.stage"}})
                else:
                    must.append({"term": {"state.stage.exact": self._stage}})

        if self._reviewer is not None:
            if self._reviewer != WorkflowControl.ANY:
                if self._reviewer == WorkflowControl.UNASSIGNED:
                    must_not.append({"exists": {"field": "state.reviewer"}})
                elif self._reviewer == WorkflowControl.ASSIGNED:
                    must.append({"exists": {"field": "state.reviewer"}})
                else:
                    must.append({"term": {"state.reviewer.exact": self._reviewer}})

        bool = {}
        if len(must) > 0:
            bool["must"] = must
        if len(must_not) > 0:
            bool["must_not"] = must_not
        q = {"query": {"bool": bool}}

        q["sort"] = {"created_date": {"order": "asc"}}

        return q
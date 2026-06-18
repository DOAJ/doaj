from copy import deepcopy
from datetime import datetime
from typing import Union

from portality.dao import DomainObject
from portality.lib import es_data_mapping, dates
from portality.lib.coerce import COERCE_MAP
from portality.lib.seamless import SeamlessMixin
from portality.core import app
from portality.models import Application, Account

import json

TRIAGE_FIELD = {
    "fields": {
        "answer": {"coerce": "unicode"},
        "compliant": {"coerce": "bool"},
        "sv": {"coerce": "integer"},
    },
    "lists": {
        "note_ids": {"contains": "field", "coerce": "unicode"},
        "changes": {"contains": "object"},
    },
    "objects": [
        "changes"
    ],
    "structs": {
        "changes": {
            "audit_id": {"coerce": "unicode"},
            "note_id": {"coerce": "unicode"},
        }
    }
}

TRIAGE_FIELD_WITH_EXCEPTIONS = deepcopy(TRIAGE_FIELD)
TRIAGE_FIELD_WITH_EXCEPTIONS["objects"].append("exceptions")
TRIAGE_FIELD_WITH_EXCEPTIONS["structs"]["exceptions"] = {}

DATABASE_NOT_REMOVED_NO_EMBARGO_FIELD = deepcopy(TRIAGE_FIELD_WITH_EXCEPTIONS)
DATABASE_NOT_REMOVED_NO_EMBARGO_FIELD["structs"]["exceptions"] = {
    "fields": {
        "ignore_embargo": {"coerce": "bool"},#b1a
        "website_unavailable": {"coerce": "bool"},#b1b
        "content_volume": {"coerce": "bool"} #b1c
    }
}

DATABASE_NO_ACTIVE_EMBARGO_FIELD = deepcopy(TRIAGE_FIELD_WITH_EXCEPTIONS)
DATABASE_NO_ACTIVE_EMBARGO_FIELD["structs"]["exceptions"] = {
    "fields": {
        "confirmed_issn": {"coerce": "bool"},#b2a
        "ignore_embargo": {"coerce": "bool"},#b2b
        "website_unavailable": {"coerce": "bool"},#b2c
        "content_volume": {"coerce": "bool"}#b2d
    }
}

CONTENT_NOT_NEW_OR_FLIPPED = deepcopy(TRIAGE_FIELD_WITH_EXCEPTIONS)
CONTENT_NOT_NEW_OR_FLIPPED["structs"]["exceptions"] = {
    "fields": {
        "publishing_history": {"coerce": "bool"} #e6a
    }
}


TRIAGE_STRUCT = {
    "fields": {
        "has_minimal_review": {"coerce": "bool"},
        "total_sv": {"coerce": "integer"},
        "last_visited_question": {"coerce": "unicode"},
    },
    "objects": ["questions"],
    "structs": {
        "questions": {
            "fields": {
                "admin_special_exception": {"coerce": "unicode"}
            },
            "objects": [
                "ethics_not_excluded", #a1
                "ethics_no_nonstandard_metrics", #a2
                "ethics_no_fake_impact", #a3
                "ethics_no_false_doaj_claim", #a4
                "ethics_ttp_gt_3wk", #a5
                "ethics_no_suspicious_ties", #a6

                "database_not_removed_no_embargo", #b1
                "database_no_active_embargo", #b2
                "database_not_listed", #b3
                "database_not_duplicate", #b4

                "issn_at_least_one", #c1
                "issn_journal_name_match", #c2
                "issn_no_continuation", #c3

                "website_working", #d1
                "website_distinct_urls", #d2
                "website_oa_policy", #d3
                "website_copyright_terms", #d4

                "content_no_registration", #e1
                "content_no_barrier", #e2
                "content_sufficient_volume", #e3
                "content_unique_article_urls", #e4
                "content_html_pdf", #e5
                "content_not_new_or_flipped", #e6

                "admin_metadata_accurate", #f1
                "admin_special_exception", #f2
            ],
            "structs": {
                "ethics_not_excluded": TRIAGE_FIELD,
                "ethics_no_nonstandard_metrics": TRIAGE_FIELD,
                "ethics_no_fake_impact": TRIAGE_FIELD,
                "ethics_no_false_doaj_claim": TRIAGE_FIELD,
                "ethics_ttp_gt_3wk": TRIAGE_FIELD,
                "ethics_no_suspicious_ties": TRIAGE_FIELD,

                "database_not_removed_no_embargo": DATABASE_NOT_REMOVED_NO_EMBARGO_FIELD,
                "database_no_active_embargo": DATABASE_NO_ACTIVE_EMBARGO_FIELD,
                "database_not_listed": TRIAGE_FIELD,
                "database_not_duplicate": TRIAGE_FIELD,

                "issn_at_least_one": TRIAGE_FIELD,
                "issn_journal_name_match": TRIAGE_FIELD,
                "issn_no_continuation": TRIAGE_FIELD,

                "website_working": TRIAGE_FIELD,
                "website_distinct_urls": TRIAGE_FIELD,
                "website_oa_policy": TRIAGE_FIELD,
                "website_copyright_terms": TRIAGE_FIELD,

                "content_no_registration": TRIAGE_FIELD,
                "content_no_barrier": TRIAGE_FIELD,
                "content_sufficient_volume": TRIAGE_FIELD,
                "content_unique_article_urls": TRIAGE_FIELD,
                "content_html_pdf": TRIAGE_FIELD,
                "content_not_new_or_flipped": CONTENT_NOT_NEW_OR_FLIPPED,

                "admin_metadata_accurate": TRIAGE_FIELD
            }
        }
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
        "audit": {"contains": "object"},
        "labels": {"contains": "field", "coerce": "unicode"}
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
        self._notes_cache = {}

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

    def save(self, *args, **kwargs):
        # all notes in the cache should get saved
        for id, n in self._notes_cache:
            n.save()
        super(WorkflowControl, self).save(*args, **kwargs)

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
    def triage(self) -> "Triage":
        t = self.__seamless__.get_single("modules.triage")
        if t is None:
            self.__seamless__.set_single("modules.triage", {})
            t = self.__seamless__.get_single("modules.triage")
        return Triage(t, self)

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

    ##################################
    ## labelling

    @property
    def labels(self):
        return self.__seamless__.get_list("labels")

    @labels.setter
    def labels(self, val):
        self.__seamless__.set_with_struct("labels", val)

    def add_label(self, label:str):
        self.__seamless__.add_to_list("labels", label, unique=True)

    def remove_label(self, label:str):
        self.__seamless__.delete_from_list("labels", label)

    ###################################
    ## Model behaviour

    def cache_note(self, note:"Note"):
        self._notes_cache[note.id] = note


class TriageField(SeamlessMixin):
    __SEAMLESS_STRUCT__ = TRIAGE_FIELD
    __SEAMLESS_COERCE__ = COERCE_MAP

    def __init__(self, raw=None, parent:"Triage"=None, **kwargs):
        super(TriageField, self).__init__(raw=raw, **kwargs)
        self._parent = parent
        self._notes = {}

    @property
    def answer(self) -> str:
        return self.__seamless__.get_single("answer")

    @answer.setter
    def answer(self, val):
        self.__seamless__.set_single("answer", val)

    @property
    def compliant(self) -> bool:
        return self.__seamless__.get_single("compliant")

    @compliant.setter
    def compliant(self, val):
        self.__seamless__.set_single("compliant", val)

    @property
    def severity_value(self) -> int:
        return self.__seamless__.get_single("sv")

    @severity_value.setter
    def severity_value(self, val):
        self.__seamless__.set_single("sv", val)

    @property
    def note_ids(self):
        return self.__seamless__.get_list("note_ids")

    @property
    def changes(self):
        return self.__seamless__.get_list("changes")

    @property
    def notes(self):
        from portality.models import Note
        for nid in self.note_ids:
            if nid not in self._notes:
                # TODO: merge in separate notes code
                self._notes[nid] = Note.pull(nid)
        return self._notes

    def add_note(self, note:"Note"):
        if note.id is None:
            note.set_id(note.makeid())
        self._notes[note.id] = note
        self.__seamless__.add_to_list("note_ids", note.id, unique=True)
        if self._parent is not None:
            self._parent.cache_note(note)


class DatabaseNotRemovedNoEmbargoField(TriageField):
    __SEAMLESS_STRUCT__ = DATABASE_NOT_REMOVED_NO_EMBARGO_FIELD

    @property
    def ignore_embargo(self):
        return self.__seamless__.get_single("exceptions.ignore_embargo")

    @ignore_embargo.setter
    def ignore_embargo(self, val):
        self.__seamless__.set_with_struct("exceptions.ignore_embargo", val)

class Triage(SeamlessMixin):
    __SEAMLESS_STRUCT__ = TRIAGE_STRUCT
    __SEAMLESS_COERCE__ = COERCE_MAP

    def __init__(self, raw=None, parent:WorkflowControl=None, **kwargs):
        super(Triage, self).__init__(raw=raw, **kwargs)
        self._parent = parent

    @property
    def data(self):
        return self.__seamless__.data

    def cache_note(self, note:"Note"):
        if self._parent is not None:
            self._parent.cache_note(note)

    @property
    def has_minimal_review(self):
        return self.__seamless__.get_single("has_minimal_review")

    @has_minimal_review.setter
    def has_minimal_review(self, val):
        self.__seamless__.set_single("has_minimal_review", val)

    def _get_triage_field(self, field):
        t = self.__seamless__.get_single(f"questions.{field}")
        if t is None:
            self.__seamless__.set_single(f"questions.{field}", {})
            t = self.__seamless__.get_single(f"questions.{field}")
        return TriageField(t, self)

    def _calculate_severity_value(self):
        total = 0
        for k, v in self.__seamless__.get_single("questions", []).items():
            if "sv" in v:
                total += v["sv"]
        self.__seamless__.set_with_struct("total_sv", total)

    @property
    def total_severity_value(self):
        return self.__seamless__.get_single("total_sv")

    def _set_question(self, field:str, value:bool, sv:int=None, exception:int=None, note:"Note"=None):
        obj = {
            "value": value,
        }
        if sv is not None:
            obj["sv"] = sv
        if exception is not None:
            obj["exception"] = exception
        if note is not None:
            obj["note"] = note.id

        self.__seamless__.set_with_struct(f"questions.{field}", obj)
        self._calculate_severity_value()

    @property
    def ethics_not_excluded(self) -> TriageField:
        return self._get_triage_field("ethics_not_excluded")

    @property
    def ethics_no_nonstandard_metrics(self) -> TriageField:
        return self._get_triage_field("ethics_no_nonstandard_metrics")

    @property
    def ethics_no_fake_impact(self) -> TriageField:
        return self._get_triage_field("ethics_no_fake_impact")

    @property
    def ethics_no_false_doaj_claim(self) -> TriageField:
        return self._get_triage_field("ethics_no_false_doaj_claim")

    @property
    def ethics_no_suspicious_ties(self) -> TriageField:
        return self._get_triage_field("ethics_no_suspicious_ties")

    @property
    def issn_at_least_one(self) -> TriageField:
        return self._get_triage_field("issn_at_least_one")

    @property
    def database_not_removed_no_embargo(self):
        return None


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
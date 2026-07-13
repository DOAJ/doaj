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
        "exception": {"coerce": "bool"},
        "note_id": {"coerce": "unicode"},
    },
    "lists": {
        "changes": {"contains": "object"},
    },
    "structs": {
        "changes": {
            "audit_id": {"coerce": "unicode"},
            "note_id": {"coerce": "unicode"},
        }
    }
}

SPECIAL_EXCEPTION_TRIAGE_FIELD = deepcopy(TRIAGE_FIELD)
SPECIAL_EXCEPTION_TRIAGE_FIELD["lists"]["special_exceptions"] = {"contains": "field", "coerce": "unicode"}
SPECIAL_EXCEPTION_TRIAGE_FIELD["fields"]["special_exception_other"] = {"coerce": "unicode"}

TRIAGE_STRUCT = {
    "fields": {
        "total_sv": {"coerce": "integer"},
        "last_visited_question": {"coerce": "unicode"},
    },
    "objects": ["questions", "recommendation"],
    "structs": {
        "recommendation": {
            "fields": {
                "code": {"coerce": "unicode"},
            },
            "lists": {
                "reasons": {"contains": "object"}
            },
            "structs": {
                "reasons": {
                    "fields": {
                        "question": {"coerce": "unicode"},
                        "answer": {"coerce": "unicode"},
                        "sv": {"coerce": "integer"}
                    },
                    "lists": {
                        "exception": {"contains": "field", "coerce": "unicode"}
                    }
                }
            }
        },
        "questions": {
            "fields": {
                "admin_special_exception": {"coerce": "unicode"}
            },
            "objects": [
                "ethics_not_excluded",
                "ethics_no_nonstandard_metrics",
                "ethics_no_fake_impact",
                "ethics_no_false_doaj_claim",
                "ethics_no_suspicious_ties",
                "ethics_submission_to_publication_time",

                "database_withdrawn",
                # "database_withdrawn_exception_ignore_embargo",
                # "database_withdrawn_exception_website_unavailable",
                # "database_withdrawn_exception_content",
                "database_embargo",
                # "database_embargo_exception_issn",
                # "database_embargo_exception_maned",
                # "database_embargo_exception_website",
                # "database_embargo_exception_content",
                "database_not_listed",
                "database_not_duplicate",

                "issn_at_least_one",
                "issn_country_match",
                "issn_title_match",
                "issn_continuation",

                "website_working",
                "website_issn",
                "website_url",
                "website_license_policy",
                "website_copyright",

                "content_no_login",
                "content_no_embargo",
                "content_publish_enough",
                "content_unique_link",
                "content_format",
                "content_new_journal",

                "admin_metadata_review",
                "admin_special_exception",
            ],
            "structs": {
                "ethics_not_excluded": TRIAGE_FIELD,
                "ethics_no_nonstandard_metrics": TRIAGE_FIELD,
                "ethics_no_fake_impact": TRIAGE_FIELD,
                "ethics_no_false_doaj_claim": TRIAGE_FIELD,
                "ethics_no_suspicious_ties": TRIAGE_FIELD,
                "ethics_submission_to_publication_time": TRIAGE_FIELD,

                "database_withdrawn": SPECIAL_EXCEPTION_TRIAGE_FIELD,
                #"database_withdrawn_exception_ignore_embargo": TRIAGE_FIELD,
                #"database_withdrawn_exception_website_unavailable": TRIAGE_FIELD,
                #"database_withdrawn_exception_content": TRIAGE_FIELD,
                "database_embargo": SPECIAL_EXCEPTION_TRIAGE_FIELD,
                # "database_embargo_exception_issn": TRIAGE_FIELD,
                # "database_embargo_exception_maned": TRIAGE_FIELD,
                # "database_embargo_exception_website": TRIAGE_FIELD,
                # "database_embargo_exception_content": TRIAGE_FIELD,
                "database_not_listed": TRIAGE_FIELD,
                "database_not_duplicate": TRIAGE_FIELD,

                "issn_at_least_one": TRIAGE_FIELD,
                "issn_country_match": TRIAGE_FIELD,
                "issn_title_match": TRIAGE_FIELD,
                "issn_continuation": TRIAGE_FIELD,

                "website_working": TRIAGE_FIELD,
                "website_issn": TRIAGE_FIELD,
                "website_url": TRIAGE_FIELD,
                "website_license_policy": TRIAGE_FIELD,
                "website_copyright": TRIAGE_FIELD,

                "content_no_login": TRIAGE_FIELD,
                "content_no_embargo": TRIAGE_FIELD,
                "content_publish_enough": TRIAGE_FIELD,
                "content_unique_link": TRIAGE_FIELD,
                "content_format": TRIAGE_FIELD,
                "content_new_journal": SPECIAL_EXCEPTION_TRIAGE_FIELD,

                "admin_metadata_review": TRIAGE_FIELD,
                "admin_special_exception": SPECIAL_EXCEPTION_TRIAGE_FIELD
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
        if self.id is None:
            self.set_id(self.makeid())
        # all notes in the cache should get saved
        for id, n in self._notes_cache.items():
            n.resource_id = self.id
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

    @triage.setter
    def triage(self, val:Union[dict, "Triage"]):
        # note that if given a Triage object this copies the contents, as the old
        # object will be part of some other WorkflowControl object, and the mixed
        # ownership can cause confusion
        if isinstance(val, Triage):
            data = deepcopy(val.data)
            self.__seamless__.set_single("modules.triage", data)
            # if we are given an object which has notes cached, take those notes into the
            # cache of this object, so we can save them
            self.cache_notes(val.cached_notes)
        else:
            self.__seamless__.set_with_struct("modules.triage", val)

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

    def cache_notes(self, notes:dict):
        for id, n in notes.items():
            self.cache_note(n)

    @property
    def cached_notes(self):
        return self._notes_cache

class TriageField(SeamlessMixin):
    __SEAMLESS_STRUCT__ = TRIAGE_FIELD
    __SEAMLESS_COERCE__ = COERCE_MAP

    def __init__(self, name, raw=None, parent:"Triage"=None, **kwargs):
        super(TriageField, self).__init__(raw=raw, **kwargs)
        self._name = name
        self._parent = parent
        self._note = None

    @property
    def name(self):
        return self._name

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
        return self.__seamless__.get_single("sv", default=0)

    @severity_value.setter
    def severity_value(self, val):
        self.__seamless__.set_single("sv", val)

    @property
    def exception(self) -> bool:
        return self.__seamless__.get_single("exception", default=[])

    @exception.setter
    def exception(self, val:bool):
        self.__seamless__.set_single("exception", val)

    @property
    def note_id(self):
        return self.__seamless__.get_single("note_id")

    @property
    def changes(self):
        return self.__seamless__.get_list("changes")

    @property
    def note(self):
        from portality.models import Note
        if self._note is None and self.note_id is not None:
            self._note = Note.pull(self.note_id)
        return self._note

    @note.setter
    def note(self, note:"Note"):
        if note.id is None:
            note.set_id(note.makeid())
        self._note = note
        self.__seamless__.set_single("note_id", note.id)
        if self._parent is not None:
            self._parent.cache_note(note)

class SpecialExceptionTriageField(TriageField):
    __SEAMLESS_STRUCT__ = SPECIAL_EXCEPTION_TRIAGE_FIELD

    @property
    def special_exceptions(self):
        return self.__seamless__.get_list("special_exceptions")

    @special_exceptions.setter
    def special_exceptions(self, val):
        self.__seamless__.set_with_struct("special_exceptions", val)

    @property
    def special_exception_other(self):
        return self.__seamless__.get_single("special_exception_other")

    @special_exception_other.setter
    def special_exception_other(self, val):
        self.__seamless__.set_with_struct("special_exception_other", val)


class Triage(SeamlessMixin):
    __SEAMLESS_STRUCT__ = TRIAGE_STRUCT
    __SEAMLESS_COERCE__ = COERCE_MAP

    EXCEPTION_QUESTIONS = [
        "admin_special_exception",
        "database_withdrawn",
        "database_embargo",
        "content_new_journal"
    ]

    def __init__(self, raw=None, parent:WorkflowControl=None, **kwargs):
        super(Triage, self).__init__(raw=raw, **kwargs)
        self._parent = parent
        self._notes_cache = {}

    @property
    def data(self):
        return self.__seamless__.data

    def cache_note(self, note:"Note"):
        # cache the note at this level and pass it up.  This means that if
        # the object gets detached in some way, the cache for everything
        # beneath it is in place, and can be used to inform the new
        # owner of the triage data
        self._notes_cache[note.id] = note
        if self._parent is not None:
            self._parent.cache_note(note)

    @property
    def cached_notes(self):
        return self._notes_cache

    @property
    def review_complete(self):
        check_fields = TRIAGE_STRUCT["structs"]["questions"]["objects"]
        for f in check_fields:
            c = self.__seamless__.get_single(f"questions.{f}.compliant")
            if c is None:
                return False
        return True

    @review_complete.setter
    def review_complete(self, val):
        self.__seamless__.set_single("has_minimal_review", val)

    def recommend(self, code:str, reasons:list[dict]):
        obj = {
            "code": code,
            "reasons": reasons
        }
        self.__seamless__.set_with_struct("recommendation", obj)

    @property
    def recommendation(self):
        return self.__seamless__.get_single("recommendation")

    def _get_triage_field(self, field):
        t = self.__seamless__.get_single(f"questions.{field}")
        if t is None:
            self.__seamless__.set_single(f"questions.{field}", {})
            t = self.__seamless__.get_single(f"questions.{field}")

        if field in self.EXCEPTION_QUESTIONS:
            return SpecialExceptionTriageField(field, t, self)

        return TriageField(field, t, self)

    def _set_triage_field(self, field:str, val:Union[dict, "TriageField"]):
        # note that if given a TriageField object this copies the contents, as the old
        # object will be part of some other WorkflowControl object, and the mixed
        # ownership can cause confusion
        if isinstance(val, TriageField):
            data = deepcopy(val.data)
            self.__seamless__.set_single(f"questions.{field}", data)
            # if we are given an object which has notes cached, take those notes into the
            # cache of this object, so we can save them
            self.cache_note(val.note)
        else:
            self.__seamless__.set_with_struct(f"questions.{field}", val)

    def _calculate_severity_value(self):
        total = 0
        for k, v in self.__seamless__.get_single("questions", default=[]).items():
            if "sv" in v:
                total += v["sv"]
        self.__seamless__.set_with_struct("total_sv", total)

    @property
    def total_severity_value(self):
        self._calculate_severity_value()
        return self.__seamless__.get_single("total_sv", default=0)

    def get_fields_with_non_zero_severity_value(self):
        reg = []
        questions = self.__seamless__.get_single("questions")
        for name, field in questions.items():
            if field.get("sv", 0) > 0:
                reg.append(self._get_triage_field(name))
        return reg

    def _set_question(self, field:str, value:bool, sv:int=None, exception:bool=None, note:"Note"=None):
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

    @ethics_not_excluded.setter
    def ethics_not_excluded(self, field:TriageField):
        self._set_triage_field("ethics_not_excluded", field)

    @property
    def ethics_no_nonstandard_metrics(self) -> TriageField:
        return self._get_triage_field("ethics_no_nonstandard_metrics")

    @ethics_no_nonstandard_metrics.setter
    def ethics_no_nonstandard_metrics(self, field:TriageField):
        self._set_triage_field("ethics_no_nonstandard_metrics", field)

    @property
    def ethics_no_fake_impact(self) -> TriageField:
        return self._get_triage_field("ethics_no_fake_impact")

    @ethics_no_fake_impact.setter
    def ethics_no_fake_impact(self, field:TriageField):
        self._set_triage_field("ethics_no_fake_impact", field)

    @property
    def ethics_no_false_doaj_claim(self) -> TriageField:
        return self._get_triage_field("ethics_no_false_doaj_claim")

    @ethics_no_false_doaj_claim.setter
    def ethics_no_false_doaj_claim(self, field:TriageField):
        self._set_triage_field("ethics_no_false_doaj_claim", field)

    @property
    def ethics_no_suspicious_ties(self) -> TriageField:
        return self._get_triage_field("ethics_no_suspicious_ties")

    @ethics_no_suspicious_ties.setter
    def ethics_no_suspicious_ties(self, field:TriageField):
        self._set_triage_field("ethics_no_suspicious_ties", field)

    @property
    def ethics_submission_to_publication_time(self) -> TriageField:
        return self._get_triage_field("ethics_submission_to_publication_time")

    @ethics_submission_to_publication_time.setter
    def ethics_submission_to_publication_time(self, field:TriageField):
        self._set_triage_field("ethics_submission_to_publication_time", field)

    @property
    def database_withdrawn(self):
        return self._get_triage_field("database_withdrawn")

    # @database_withdrawn.setter
    # def database_withdrawn(self, field:TriageField):
    #     self._set_triage_field("database_withdrawn", field)
    #
    # @property
    # def database_withdrawn_exception_ignore_embargo(self):
    #     return self._get_triage_field("database_withdrawn_exception_ignore_embargo")
    #
    # @database_withdrawn_exception_ignore_embargo.setter
    # def database_withdrawn_exception_ignore_embargo(self, field:TriageField):
    #     self._set_triage_field("database_withdrawn_exception_ignore_embargo", field)
    #
    # @property
    # def database_withdrawn_exception_website_unavailable(self):
    #     return self._get_triage_field("database_withdrawn_exception_website_unavailable")
    #
    # @database_withdrawn_exception_website_unavailable.setter
    # def database_withdrawn_exception_website_unavailable(self, field:TriageField):
    #     self._set_triage_field("database_withdrawn_exception_website_unavailable", field)
    #
    # @property
    # def database_withdrawn_exception_content(self):
    #     return self._get_triage_field("database_withdrawn_exception_content")
    #
    # @database_withdrawn_exception_content.setter
    # def database_withdrawn_exception_content(self, field:TriageField):
    #     self._set_triage_field("database_withdrawn_exception_content", field)

    @property
    def database_embargo(self):
        return self._get_triage_field("database_embargo")

    @database_embargo.setter
    def database_embargo(self, field:TriageField):
        self._set_triage_field("database_embargo", field)

    # @property
    # def database_embargo_exception_issn(self):
    #     return self._get_triage_field("database_embargo_exception_issn")
    #
    # @database_embargo_exception_issn.setter
    # def database_embargo_exception_issn(self, field:TriageField):
    #     self._set_triage_field("database_embargo_exception_issn", field)
    #
    # @property
    # def database_embargo_exception_maned(self):
    #     return self._get_triage_field("database_embargo_exception_maned")
    #
    # @database_embargo_exception_maned.setter
    # def database_embargo_exception_maned(self, field:TriageField):
    #     self._set_triage_field("database_embargo_exception_maned", field)
    #
    # @property
    # def database_embargo_exception_website(self):
    #     return self._get_triage_field("database_embargo_exception_website")
    #
    # @database_embargo_exception_website.setter
    # def database_embargo_exception_website(self, field:TriageField):
    #     self._set_triage_field("database_embargo_exception_website", field)
    #
    # @property
    # def database_embargo_exception_content(self):
    #     return self._get_triage_field("database_embargo_exception_content")
    #
    # @database_embargo_exception_content.setter
    # def database_embargo_exception_content(self, field:TriageField):
    #     self._set_triage_field("database_embargo_exception_content", field)

    @property
    def database_not_listed(self):
        return self._get_triage_field("database_not_listed")

    @database_not_listed.setter
    def database_not_listed(self, field:TriageField):
        self._set_triage_field("database_not_listed", field)

    @property
    def database_not_duplicate(self):
        return self._get_triage_field("database_not_duplicate")

    @database_not_duplicate.setter
    def database_not_duplicate(self, field:TriageField):
        self._set_triage_field("database_not_duplicate", field)

    @property
    def issn_at_least_one(self) -> TriageField:
        return self._get_triage_field("issn_at_least_one")

    @property
    def issn_country_match(self) -> TriageField:
        return self._get_triage_field("issn_country_match")

    @issn_country_match.setter
    def issn_country_match(self, field:TriageField):
        self._set_triage_field("issn_country_match", field)

    @property
    def issn_title_match(self) -> TriageField:
        return self._get_triage_field("issn_title_match")

    @issn_title_match.setter
    def issn_title_match(self, field:TriageField):
        self._set_triage_field("issn_title_match", field)

    @property
    def issn_continuation(self) -> TriageField:
        return self._get_triage_field("issn_continuation")

    @issn_continuation.setter
    def issn_continuation(self, field:TriageField):
        self._set_triage_field("issn_continuation", field)

    @property
    def website_working(self) -> TriageField:
        return self._get_triage_field("website_working")

    @website_working.setter
    def website_working(self, field:TriageField):
        self._set_triage_field("website_working", field)

    @property
    def website_issn(self) -> TriageField:
        return self._get_triage_field("website_issn")

    @website_issn.setter
    def website_issn(self, field:TriageField):
        self._set_triage_field("website_issn", field)

    @property
    def website_url(self) -> TriageField:
        return self._get_triage_field("website_url")

    @website_url.setter
    def website_url(self, field:TriageField):
        self._set_triage_field("website_url", field)

    @property
    def website_license_policy(self) -> TriageField:
        return self._get_triage_field("website_license_policy")

    @website_license_policy.setter
    def website_license_policy(self, field:TriageField):
        self._set_triage_field("website_license_policy", field)

    @property
    def website_copyright(self) -> TriageField:
        return self._get_triage_field("website_copyright")

    @website_copyright.setter
    def website_copyright(self, field:TriageField):
        self._set_triage_field("website_copyright", field)

    @property
    def content_no_login(self) -> TriageField:
        return self._get_triage_field("content_no_login")

    @content_no_login.setter
    def content_no_login(self, field:TriageField):
        self._set_triage_field("content_no_login", field)

    @property
    def content_no_embargo(self) -> TriageField:
        return self._get_triage_field("content_no_embargo")

    @content_no_embargo.setter
    def content_no_embargo(self, field:TriageField):
        self._set_triage_field("content_no_embargo", field)

    @property
    def content_publish_enough(self) -> TriageField:
        return self._get_triage_field("content_publish_enough")

    @content_publish_enough.setter
    def content_publish_enough(self, field:TriageField):
        self._set_triage_field("content_publish_enough", field)

    @property
    def content_unique_link(self) -> TriageField:
        return self._get_triage_field("content_unique_link")

    @content_unique_link.setter
    def content_unique_link(self, field:TriageField):
        self._set_triage_field("content_unique_link", field)

    @property
    def content_format(self) -> TriageField:
        return self._get_triage_field("content_format")

    @content_format.setter
    def content_format(self, field:TriageField):
        self._set_triage_field("content_format", field)

    @property
    def content_new_journal(self) -> TriageField:
        return self._get_triage_field("content_new_journal")

    @content_new_journal.setter
    def content_new_journal(self, field:TriageField):
        self._set_triage_field("content_new_journal", field)

    @property
    def admin_metadata_review(self) -> TriageField:
        return self._get_triage_field("admin_metadata_review")

    @admin_metadata_review.setter
    def admin_metadata_review(self, field:TriageField):
        self._set_triage_field("admin_metadata_review", field)

    @property
    def admin_special_exception(self) -> TriageField:
        return self._get_triage_field("admin_special_exception")

    @admin_special_exception.setter
    def admin_special_exception(self, field:TriageField):
        self._set_triage_field("admin_special_exception", field)

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
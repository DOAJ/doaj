from copy import deepcopy

from portality import constants
from portality.core import app
from portality.lib import es_data_mapping
from portality.models.v2 import shared_structs
from portality.models.v2.journal import JournalLikeObject
from portality.lib.coerce import COERCE_MAP

APPLICATION_STRUCT = {
    "objects" : [
        "admin", "index"
    ],

    "structs" : {
        "admin" : {
            "fields" : {
                "current_journal" : {"coerce" : "unicode"},
                "related_journal" : {"coerce" : "unicode"},
                "application_status" : {"coerce" : "unicode"},
                "date_applied" : {"coerce" : "utcdatetime"},
                "last_manual_update": {"coerce": "utcdatetime"}
            }
        },
        "index" : {
            "fields" : {
                "application_type": {"coerce": "unicode"}
            }
        }
    }
}

class Application(JournalLikeObject):
    __type__ = "application"

    __SEAMLESS_STRUCT__ = [
        shared_structs.JOURNAL_BIBJSON,
        shared_structs.SHARED_JOURNAL_LIKE,
        APPLICATION_STRUCT
    ]

    __SEAMLESS_COERCE__ = COERCE_MAP

    def __init__(self, **kwargs):
        # FIXME: hack, to deal with ES integration layer being improperly abstracted
        if "_source" in kwargs:
            kwargs = kwargs["_source"]
        super(Application, self).__init__(raw=kwargs)

    @classmethod
    def get_by_owner(cls, owner):
        q = SuggestionQuery(owner=owner)
        result = cls.query(q=q.query())
        records = [cls(**r.get("_source")) for r in result.get("hits", {}).get("hits", [])]
        return records

    @classmethod
    def delete_selected(cls, email=None, statuses=None):
        q = SuggestionQuery(email=email, statuses=statuses)
        r = cls.delete_by_query(q.query())

    @classmethod
    def list_by_status(cls, status):
        q = StatusQuery(status)
        return cls.iterate(q=q.query())

    @classmethod
    def find_latest_by_current_journal(cls, journal_id):
        q = CurrentJournalQuery(journal_id)
        results = cls.q2obj(q=q.query())
        if len(results) > 0:
            return results[0]
        return None

    @classmethod
    def find_all_by_related_journal(cls, journal_id):
        q = RelatedJournalQuery(journal_id, size=1000)
        return cls.q2obj(q=q.query())

    def mappings(self):
        return es_data_mapping.create_mapping(self.__seamless_struct__.raw, MAPPING_OPTS)

    @property
    def current_journal(self):
        return self.__seamless__.get_single("admin.current_journal")

    def set_current_journal(self, journal_id):
        self.__seamless__.set_with_struct("admin.current_journal", journal_id)

    def remove_current_journal(self):
        self.__seamless__.delete("admin.current_journal")

    @property
    def related_journal(self):
        return self.__seamless__.get_single("admin.related_journal")

    def set_related_journal(self, journal_id):
        self.__seamless__.set_with_struct("admin.related_journal", journal_id)

    def remove_related_journal(self):
        self.__seamless__.delete("admin.related_journal")

    @property
    def application_status(self):
        return self.__seamless__.get_single("admin.application_status")

    def set_application_status(self, val):
        self.__seamless__.set_with_struct("admin.application_status", val)

    @property
    def date_applied(self):
        return self.__seamless__.get_single("admin.date_applied")

    @date_applied.setter
    def date_applied(self, val):
        self.__seamless__.set_with_struct("admin.date_applied", val)

    def _sync_owner_to_journal(self):
        if self.current_journal is None:
            return
        from portality.models.v2.journal import Journal
        cj = Journal.pull(self.current_journal)
        if cj is not None and cj.owner != self.owner:
            cj.set_owner(self.owner)
            cj.save(sync_owner=False)

    def _generate_index(self):
        super(Application, self)._generate_index()

        if self.current_journal is not None:
            self.__seamless__.set_with_struct("index.application_type", constants.APPLICATION_TYPE_UPDATE_REQUEST)
        elif self.application_status in [constants.APPLICATION_STATUS_ACCEPTED, constants.APPLICATION_STATUS_REJECTED]:
            self.__seamless__.set_with_struct("index.application_type", constants.APPLICATION_TYPE_FINISHED)
        else:
            self.__seamless__.set_with_struct("index.application_type", constants.APPLICATION_TYPE_NEW_APPLICATION)

    def prep(self, is_update=True):
        self._generate_index()
        if is_update:
            self.set_last_updated()

    def save(self, sync_owner=True, **kwargs):
        self.prep()
        self.verify_against_struct()
        if sync_owner:
            self._sync_owner_to_journal()
        return super(Application, self).save(**kwargs)


    #########################################################
    ## DEPRECATED METHODS

    @property
    def suggested_on(self):
        return self.date_applied

    @suggested_on.setter
    def suggested_on(self, val):
        self.date_applied = val

    @property
    def suggester(self):
        owner = self.owner
        if owner is None:
            return None
        from portality.models import Account
        oacc = Account.pull(owner)
        if oacc is None:
            return None
        return {
            "name" : owner,
            "email" : oacc.email
        }


class DraftApplication(Application):
    __type__ = "draft_application"

    __SEAMLESS_APPLY_STRUCT_ON_INIT__ = False
    __SEAMLESS_CHECK_REQUIRED_ON_INIT__ = False


MAPPING_OPTS = {
    "dynamic": None,
    "coerces": app.config["DATAOBJ_TO_MAPPING_DEFAULTS"],
    "exceptions": {
        "admin.notes.note": {
                    "type": "string",
                    "index": "not_analyzed",
                    "include_in_all": False
        }
    }
}


class SuggestionQuery(object):
    _base_query = { "query" : { "bool" : {"must" : []}}}
    _email_term = {"term" : {"admin.applicant.email.exact" : "<email address>"}}
    _status_terms = {"terms" : {"admin.application_status.exact" : ["<list of statuses>"]}}
    _owner_term = {"term" : {"admin.owner.exact" : "<the owner id>"}}

    def __init__(self, email=None, statuses=None, owner=None):
        self.email = email
        self.owner = owner
        if statuses:
            self.statuses = statuses
        else:
            self.statuses = []

    def query(self):
        q = deepcopy(self._base_query)
        if self.email:
            et = deepcopy(self._email_term)
            et["term"]["admin.applicant.email.exact"] = self.email
            q["query"]["bool"]["must"].append(et)
        if self.statuses and len(self.statuses) > 0:
            st = deepcopy(self._status_terms)
            st["terms"]["admin.application_status.exact"] = self.statuses
            q["query"]["bool"]["must"].append(st)

        if self.owner is not None:
            ot = deepcopy(self._owner_term)
            ot["term"]["admin.owner.exact"] = self.owner
            q["query"]["bool"]["must"].append(ot)
        return q

class OwnerStatusQuery(object):
    base_query = {
        "query" : {
            "bool" : {
                "must" : []
            }
        },
        "sort" : [
            {"created_date" : "desc"}
        ],
        "size" : 10
    }
    def __init__(self, owner, statuses, size=10):
        self._query = deepcopy(self.base_query)
        owner_term = {"match" : {"owner" : owner}}
        self._query["query"]["bool"]["must"].append(owner_term)
        status_term = {"terms" : {"admin.application_status.exact" : statuses}}
        self._query["query"]["bool"]["must"].append(status_term)
        self._query["size"] = size

    def query(self):
        return self._query

class StatusQuery(object):

    def __init__(self, statuses):
        if not isinstance(statuses, list):
            statuses = [statuses]
        self.statuses = statuses

    def query(self):
        return {
            "query" : {
                "bool" : {
                    "must" : [
                        {"terms" : {"admin.application_status.exact" : self.statuses}}
                    ]
                }
            }
        }

class CurrentJournalQuery(object):

    def __init__(self, journal_id, size=1):
        self.journal_id = journal_id
        self.size = size

    def query(self):
        return {
            "query" : {
                "bool" : {
                    "must" : [
                        {"term" : {"admin.current_journal.exact" : self.journal_id}}
                    ]
                }
            },
            "sort" : [
                {"created_date" : {"order" : "desc"}}
            ],
            "size" : self.size
        }

class RelatedJournalQuery(object):

    def __init__(self, journal_id, size=1):
        self.journal_id = journal_id
        self.size = size

    def query(self):
        return {
            "query" : {
                "bool" : {
                    "must" : [
                        {"term" : {"admin.related_journal.exact" : self.journal_id}}
                    ]
                }
            },
            "sort" : [
                {"created_date" : {"order" : "asc"}}
            ],
            "size" : self.size
        }
from copy import deepcopy

from portality import constants
from portality.core import app
from portality.lib import es_data_mapping
from portality.models.v2 import shared_structs
from portality.models.v2.journal import JournalLikeObject, Journal
from portality.lib.coerce import COERCE_MAP
from portality.dao import DomainObject

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
                "application_type" : {
                    "coerce" : "unicode",
                    "allowed_values" : [
                        constants.APPLICATION_TYPE_NEW_APPLICATION,
                        constants.APPLICATION_TYPE_UPDATE_REQUEST
                    ]
                }
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
        if self.application_type is None:
            if self.current_journal:
                self.set_is_update_request(True)
            else:
                self.set_is_update_request(False)

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

    @classmethod
    def assignment_to_editor_groups(cls, egs):
        q = AssignedEditorGroupsQuery([eg.name for eg in egs])
        res = cls.query(q.query())
        buckets = res.get("aggregations", {}).get("editor_groups", {}).get("buckets", [])
        assignments = {}
        for b in buckets:
            assignments[b.get("key")] = b.get("doc_count")
        return assignments

    def mappings(self):
        return es_data_mapping.create_mapping(self.__seamless_struct__.raw, MAPPING_OPTS)

    @property
    def application_type(self):
        return self.__seamless__.get_single("admin.application_type")

    @application_type.setter
    def application_type(self, val):
        self.__seamless__.set_with_struct("admin.application_type", val)

    def set_is_update_request(self, val):
        application_type = constants.APPLICATION_TYPE_UPDATE_REQUEST if val is True else constants.APPLICATION_TYPE_NEW_APPLICATION
        self.application_type = application_type

    @property
    def current_journal(self):
        return self.__seamless__.get_single("admin.current_journal")

    def set_current_journal(self, journal_id):
        # anything that has a current journal is, by definition, an update request
        self.set_is_update_request(True)
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
    def related_journal_object(self):
        if self.related_journal:
            return Journal.pull(self.related_journal)
        return None

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

        # index_record_type = None
        # if self.application_type == constants.APPLICATION_TYPE_NEW_APPLICATION:
        #     if self.application_status in [constants.APPLICATION_STATUS_REJECTED, constants.APPLICATION_STATUS_ACCEPTED]:
        #         index_record_type = constants.INDEX_RECORD_TYPE_NEW_APPLICATION_FINISHED
        #     else:
        #         index_record_type = constants.INDEX_RECORD_TYPE_NEW_APPLICATION_UNFINISHED
        # elif self.application_type == constants.APPLICATION_TYPE_UPDATE_REQUEST:
        #     if self.application_status in [constants.APPLICATION_STATUS_REJECTED, constants.APPLICATION_STATUS_ACCEPTED]:
        #         index_record_type = constants.INDEX_RECORD_TYPE_UPDATE_REQUEST_FINISHED
        #     else:
        #         index_record_type = constants.INDEX_RECORD_TYPE_UPDATE_REQUEST_UNFINISHED
        # if index_record_type is not None:
        #     self.__seamless__.set_with_struct("index.application_type", index_record_type)

        # FIXME: Temporary partial reversion of an indexing change (this index.application_type data is still being used
        # in applications search)
        if self.current_journal is not None:
            self.__seamless__.set_with_struct("index.application_type", "update request")
        elif self.application_status in [constants.APPLICATION_STATUS_ACCEPTED, constants.APPLICATION_STATUS_REJECTED]:
            self.__seamless__.set_with_struct("index.application_type", "finished application/update")
        else:
            self.__seamless__.set_with_struct("index.application_type", "new application")


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



class AllPublisherApplications(DomainObject):
    __type__ = "draft_application,application"


MAPPING_OPTS = {
    "dynamic": None,
    "coerces": app.config["DATAOBJ_TO_MAPPING_DEFAULTS"],
    "exceptions": {
        "admin.notes.note": {
            "type": "text",
            "index": False,
            #"include_in_all": False        # Removed in es6 fixme: do we need to look at copy_to for the mapping?
        }
    }
}


class SuggestionQuery(object):
    _base_query = {"track_total_hits" : True, "query" : { "bool" : {"must" : []}}}
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
        "track_total_hits": True,
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
            "track_total_hits": True,
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
            "track_total_hits": True,
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
            "track_total_hits": True,
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


class AssignedEditorGroupsQuery(object):
    def __init__(self, editor_groups, application_type_name="new application"):
        self.editor_groups = editor_groups
        self.application_type_name = application_type_name

    def query(self):
        return {
            "query": {
                "bool": {
                    "must" : [
                        {"terms": {"admin.editor_group.exact": self.editor_groups}},
                        {"term" : {"index.application_type.exact": self.application_type_name}}
                    ]
                }
            },
            "size": 0,
            "aggs" : {
                "editor_groups": {
                    "terms": {
                        "field": "admin.editor_group.exact",
                        "size": len(self.editor_groups),
                        "order": {"_term" : "asc"}
                    }
                }
            }
        }
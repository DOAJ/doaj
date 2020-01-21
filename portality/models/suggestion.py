from copy import deepcopy

from portality import constants
from portality.core import app
from portality.lib import es_data_mapping
from portality.models import shared_structs
from portality.models.journal import JournalLikeObject


class Suggestion(JournalLikeObject):
    __type__ = "suggestion"

    def __init__(self, **kwargs):
        # FIXME: hack, to deal with ES integration layer being improperly abstracted
        if "_source" in kwargs:
            kwargs = kwargs["_source"]
        self._add_struct(shared_structs.SHARED_BIBJSON)
        self._add_struct(shared_structs.JOURNAL_BIBJSON_EXTENSION)
        self._add_struct(APPLICATION_STRUCT)
        super(Suggestion, self).__init__(raw=kwargs)

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
        return es_data_mapping.create_mapping(self.get_struct(), MAPPING_OPTS)

    @property
    def current_journal(self):
        return self._get_single("admin.current_journal")

    def set_current_journal(self, journal_id):
        self._set_with_struct("admin.current_journal", journal_id)

    def remove_current_journal(self):
        self._delete("admin.current_journal")

    @property
    def related_journal(self):
        return self._get_single("admin.related_journal")

    def set_related_journal(self, journal_id):
        self._set_with_struct("admin.related_journal", journal_id)

    def remove_related_journal(self):
        self._delete("admin.related_journal")

    @property
    def application_status(self):
        return self._get_single("admin.application_status")

    def set_application_status(self, val):
        self._set_with_struct("admin.application_status", val)

    ### suggestion properties (as in, the Suggestion model's "suggestion" object ###

    @property
    def suggested_on(self):
        return self._get_single("suggestion.suggested_on")

    @suggested_on.setter
    def suggested_on(self, val):
        self._set_with_struct("suggestion.suggested_on", val)

    @property
    def articles_last_year(self):
        return self._get_single("suggestion.articles_last_year")

    def set_articles_last_year(self, count, url):
        self._set_with_struct("suggestion.articles_last_year.count", count)
        self._set_with_struct("suggestion.articles_last_year.url", url)

    @property
    def article_metadata(self):
        return self._get_single("suggestion.article_metadata")

    @article_metadata.setter
    def article_metadata(self, val):
        self._set_with_struct("suggestion.article_metadata", val)

    @property
    def suggester(self):
        return self._get_single("suggestion.suggester", default={})

    def set_suggester(self, name, email):
        self._set_with_struct("suggestion.suggester.name", name)
        self._set_with_struct("suggestion.suggester.email", email)

    def _sync_owner_to_journal(self):
        if self.current_journal is None:
            return
        from portality.models import Journal
        cj = Journal.pull(self.current_journal)
        if cj is not None and cj.owner != self.owner:
            cj.set_owner(self.owner)
            cj.save(sync_owner=False)

    def _generate_index(self):
        super(Suggestion, self)._generate_index()

        if self.current_journal is not None:
            self._set_with_struct("index.application_type", constants.APPLICATION_TYPE_UPDATE_REQUEST)
        elif self.application_status in [constants.APPLICATION_STATUS_ACCEPTED, constants.APPLICATION_STATUS_REJECTED]:
            self._set_with_struct("index.application_type", constants.APPLICATION_TYPE_FINISHED)
        else:
            self._set_with_struct("index.application_type", constants.APPLICATION_TYPE_NEW_APPLICATION)

    def prep(self):
        self._generate_index()
        self.set_last_updated()

    def save(self, sync_owner=True, **kwargs):
        self.prep()
        self.check_construct()
        if sync_owner:
            self._sync_owner_to_journal()
        return super(Suggestion, self).save(**kwargs)

APPLICATION_STRUCT = {
    "fields" : {
        "id" : {"coerce" : "unicode"},
        "created_date" : {"coerce" : "utcdatetime"},
        "last_updated" : {"coerce" : "utcdatetime"},
        "last_manual_update" : {"coerce" : "utcdatetime"}
    },
    "objects" : [
        "admin", "index", "suggestion"
    ],

    "structs" : {
        "admin" : {
            "fields" : {
                "seal" : {"coerce" : "bool"},
                "bulk_upload" : {"coerce" : "unicode"},
                "owner" : {"coerce" : "unicode"},
                "editor_group" : {"coerce" : "unicode"},
                "editor" : {"coerce" : "unicode"},
                "current_journal" : {"coerce" : "unicode"},
                "related_journal" : {"coerce" : "unicode"},
                "application_status" : {"coerce" : "unicode"}
            },
            "lists" : {
                "contact" : {"contains" : "object"},
                "notes" : {"contains" : "object"}
            },
            "structs" : {
                "contact" : {
                    "fields" : {
                        "email" : {"coerce" : "unicode"},
                        "name" : {"coerce" : "unicode"}
                    }
                },
                "notes" : {
                    "fields" : {
                        "note" : {"coerce" : "unicode"},
                        "date" : {"coerce" : "utcdatetime"}
                    }
                }
            }
        },
        "index" : {
            "fields" : {
                "country" : {"coerce" : "unicode"},
                "homepage_url" : {"coerce" : "unicode"},
                "waiver_policy_url" : {"coerce" : "unicode"},
                "editorial_board_url" : {"coerce" : "unicode"},
                "aims_scope_url" : {"coerce" : "unicode"},
                "author_instructions_url" : {"coerce" : "unicode"},
                "oa_statement_url" : {"coerce" : "unicode"},
                "has_apc" : {"coerce" : "unicode"},
                "has_seal" : {"coerce" : "unicode"},
                "unpunctitle" : {"coerce" : "unicode"},
                "asciiunpunctitle" : {"coerce" : "unicode"},
                "continued" : {"coerce" : "unicode"},
                "application_type": {"coerce": "unicode"},
                "has_editor_group" : {"coerce" : "unicode"},
                "has_editor" : {"coerce" : "unicode"},
                "publisher" : {"coerce" : "unicode"}
            },
            "lists" : {
                "issn" : {"contains" : "field", "coerce" : "unicode"},
                "title" : {"contains" : "field", "coerce" : "unicode"},
                "subject" : {"contains" : "field", "coerce" : "unicode"},
                "schema_subject" : {"contains" : "field", "coerce" : "unicode"},
                "classification" : {"contains" : "field", "coerce" : "unicode"},
                "language" : {"contains" : "field", "coerce" : "unicode"},
                "license" : {"contains" : "field", "coerce" : "unicode"},
                "classification_paths" : {"contains" : "field", "coerce" : "unicode"},
                "schema_code" : {"contains" : "field", "coerce" : "unicode"}
            }
        },
        "suggestion" : {
            "fields" : {
                "article_metadata" : {"coerce" : "bool"},
                "suggested_on" : {"coerce" : "utcdatetime"}
            },
            "objects" : [
                "articles_last_year",
                "suggester"
            ],
            "structs" : {
                "suggester" : {
                    "fields" : {
                        "name" : {"coerce" : "unicode"},
                        "email" : {"coerce" : "unicode"}
                    }
                },
                "articles_last_year" : {
                    "fields" : {
                        "count" : {"coerce" : "integer"},
                        "url" : {"coerce" : "unicode"}
                    }
                }
            }
        }
    }
}

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
    _email_term = {"term" : {"suggestion.suggester.email.exact" : "<email address>"}}
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
            et["term"]["suggestion.suggester.email.exact"] = self.email
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
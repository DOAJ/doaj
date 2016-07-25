from portality.models.journal import Journal, JournalLikeObject
from portality.models import shared_structs

from copy import deepcopy

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

    def make_journal(self):
        # first make a raw copy of the content into a journal
        journal_data = deepcopy(self.data)
        if "suggestion" in journal_data:
            del journal_data['suggestion']
        if "index" in journal_data:
            del journal_data['index']
        if "admin" in journal_data and "application_status" in journal_data["admin"]:
            del journal_data['admin']['application_status']
        if "admin" in journal_data and "current_journal" in journal_data["admin"]:
            del journal_data["admin"]["current_journal"]
        if "id" in journal_data:
            del journal_data['id']
        if "created_date" in journal_data:
            del journal_data['created_date']
        if "last_updated" in journal_data:
            del journal_data['last_updated']
        if "bibjson" not in journal_data:
            journal_data["bibjson"] = {}
        journal_data['bibjson']['active'] = True

        new_j = Journal(**journal_data)

        # now deal with the fact that this could be a replacement of an existing journal
        if self.current_journal is not None:
            cj = Journal.pull(self.current_journal)

            # carry the id and the created date
            new_j.set_id(self.current_journal)
            new_j.set_created(cj.created_date)

            # set a reapplication date
            new_j.set_last_reapplication()

        return new_j


    @property
    def current_journal(self):
        return self._get_single("admin.current_journal")

    def set_current_journal(self, journal_id):
        self._set_with_struct("admin.current_journal", journal_id)

    def remove_current_journal(self):
        self._delete("admin.current_journal")

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
        if self.current_journal:
            self.data["index"]['application_type'] = 'reapplication'
        else:
            self.data["index"]['application_type'] = 'new application'

    def prep(self):
        self._generate_index()
        self.set_last_updated()

    def save(self, sync_owner=True, **kwargs):
        self.prep()
        if sync_owner:
            self._sync_owner_to_journal()
        super(Suggestion, self).save(**kwargs)

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
                "publisher" : {"coerce" : "unicode"},
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
                "application_type": {"coerce": "unicode"}
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


from portality.models import Journal
from copy import deepcopy

class Suggestion(Journal):
    __type__ = "suggestion"

    @classmethod
    def get_by_owner(cls, owner):
        q = SuggestionQuery(owner=owner)
        result = cls.query(q=q.query())
        records = [cls(**r.get("_source")) for r in result.get("hits", {}).get("hits", [])]
        return records

    def make_journal(self):
        # first make a raw copy of the content into a journal
        journal_data = deepcopy(self.data)
        if "suggestion" in journal_data:
            del journal_data['suggestion']
        if "index" in journal_data:
            del journal_data['index']
        if "admin" in journal_data and "application_status" in journal_data["admin"]:
            del journal_data['admin']['application_status']
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
            new_j.set_id(self.current_journal)
            new_j.set_last_reapplication()
            del new_j.data["admin"]["current_journal"]

        return new_j

    ###############################################################
    # Overrides on Journal methods
    ###############################################################

    # We don't want to calculate the tick on applications, only Journals
    def calculate_tick(self):
        pass

    @property
    def current_application(self):
        return None

    def set_current_application(self, application_id):
        pass

    @property
    def current_journal(self):
        return self.data.get("admin", {}).get("current_journal")

    def set_current_journal(self, journal_id):
        if "admin" not in self.data:
            self.data["admin"] = {}
        self.data["admin"]["current_journal"] = journal_id

    @classmethod
    def delete_selected(cls, email=None, statuses=None):
        q = SuggestionQuery(email=email, statuses=statuses)
        r = cls.delete_by_query(q.query())

    def _set_suggestion_property(self, name, value):
        if "suggestion" not in self.data:
            self.data["suggestion"] = {}
        self.data["suggestion"][name] = value

    ### suggestion properties (as in, the Suggestion model's "suggestion" object ###

    @property
    def suggested_by_owner(self):
        """
        Deprecated - DO NOT USE
        """
        return self.data.get("suggestion", {}).get("suggested_by_owner")

    @suggested_by_owner.setter
    def suggested_by_owner(self, val):
        """
        Deprecated - DO NOT USE
        """
        self._set_suggestion_property("suggested_by_owner", val)

    @property
    def suggested_on(self): return self.data.get("suggestion", {}).get("suggested_on")
    @suggested_on.setter
    def suggested_on(self, val): self._set_suggestion_property("suggested_on", val)

    @property
    def articles_last_year(self):
        return self.data.get("suggestion", {}).get("articles_last_year")

    def set_articles_last_year(self, count, url):
        if "suggestion" not in self.data:
            self.data["suggestion"] = {}
        if "articles_last_year" not in self.data["suggestion"]:
            self.data["suggestion"]["articles_last_year"] = {}
        self.data["suggestion"]["articles_last_year"]["count"] = count
        self.data["suggestion"]["articles_last_year"]["url"] = url

    @property
    def article_metadata(self): return self.data.get("suggestion", {}).get("article_metadata")
    @article_metadata.setter
    def article_metadata(self, val): self._set_suggestion_property("article_metadata", val)

    @property
    def description(self):
        """
        Deprecated - DO NOT USE
        """
        return self.data.get("suggestion", {}).get("description")

    @description.setter
    def description(self, val):
        """
        Deprecated - DO NOT USE
        """
        self._set_suggestion_property("description", val)

    @property
    def suggester(self): return self.data.get("suggestion", {}).get("suggester", {})
    def set_suggester(self, name, email):
        sugg = {}
        if name is not None:
            sugg["name"] = name
        if email is not None:
            sugg["email"] = email
        if name is None and email is None:
            return
        self._set_suggestion_property("suggester", sugg)

    def save(self, **kwargs):
        self.prep()
        super(Suggestion, self).save(snapshot=False, **kwargs)

class SuggestionQuery(object):
    _base_query = { "query" : { "bool" : {"must" : []}}}
    _email_term = {"term" : {"suggestion.suggester.email.exact" : "<email address>"}}
    _owner_term = {"term" : {"admin.owner.exact" : "<owner>"}}
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
        owner_term = {"term" : {"owner" : owner}}
        self._query["query"]["bool"]["must"].append(owner_term)
        status_term = {"terms" : {"admin.application_status.exact" : statuses}}
        self._query["query"]["bool"]["must"].append(status_term)
        self._query["size"] = size

    def query(self):
        return self._query


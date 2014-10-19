from portality.models import Journal
from copy import deepcopy

class Suggestion(Journal):
    __type__ = "suggestion"

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

class SuggestionQuery(object):
    _base_query = { "query" : { "bool" : {"must" : []}}}
    _email_term = {"term" : {"suggestion.suggester.email.exact" : "<email address>"}}
    _status_terms = {"terms" : {"admin.application_status.exact" : ["<list of statuses>"]}}

    def __init__(self, email, statuses):
        self.email = email
        self.statuses = statuses

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
        return q
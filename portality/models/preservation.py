from portality.dao import DomainObject
from datetime import datetime
from copy import deepcopy


class PreservationState(DomainObject):
    """~~Preservation:Model~~
    Model class for preservation feature"""
    __type__ = "preserve"

    @property
    def status(self):
        return self.data.get("status")

    @status.setter
    def status(self, value):
        self.data["status"] = value

    @property
    def filename(self):
        return self.data.get("filename")

    @property
    def owner(self):
        return self.data.get("owner")

    @property
    def background_task_id(self):
        return self.data.get("background_task_id")

    @background_task_id.setter
    def background_task_id(self, value):
        self.data["background_task_id"] = value

    @property
    def created_timestamp(self):
        if "created_date" not in self.data:
            return None
        return datetime.strptime(self.data["created_date"], "%Y-%m-%dT%H:%M:%SZ")

    @property
    def error(self):
        return self.data.get("error")

    @property
    def error_details(self):
        return self.data.get("error_details")

    @property
    def articles_info(self):
        return self.data.get("articles_info", {})

    def initiated(self, owner, filename, status="initiated"):
        self.data["filename"] = filename
        self.data["owner"] = owner
        self.data["articles_info"] = {}
        self.status = status

    def validated(self):
        self.status = "validated"

    def pending(self):
        self.status = "pending"

    def uploaded_to_ia(self):
        self.status = "uploaded"

    def failed(self, message, details=None):
        self.status = "failed"
        self.data["error"] = message
        if details is not None:
            self.data["error_details"] = details

    def partial(self):
        self.status = "partial"

    def successful_articles(self, articles_list):
        if articles_list is not None and len(articles_list) > 0:
            self.data["articles_info"]["successful_articles"] = ", ".join(articles_list)

    def unowned_articles(self, articles_list):
        if articles_list is not None and len(articles_list) > 0:
            self.data["articles_info"]["unowned_articles"] = ", ".join(articles_list)

    def no_identifier_articles(self, articles_list):
        if articles_list is not None and len(articles_list) > 0:
            self.data["articles_info"]["no_identifier_articles"] = ", ".join(articles_list)

    def unbagged_articles(self, articles_list):
        if articles_list is not None and len(articles_list) > 0:
            self.data["articles_info"]["unbagged_articles"] = ", ".join(articles_list)

    def not_found_articles(self, articles_list):
        if articles_list is not None and len(articles_list) > 0:
            self.data["articles_info"]["not_found_articles"] = ", ".join(articles_list)

    def no_files_articles(self, articles_list):
        if articles_list is not None and len(articles_list) > 0:
            self.data["articles_info"]["no_files_articles"] = ", ".join(articles_list)

    @classmethod
    def by_owner(cls, owner, size=10):
        q = OwnerFileQuery(owner)
        res = cls.query(q=q.query())
        rs = [PreservationState(**r.get("_source")) for r in res.get("hits", {}).get("hits", [])]
        return rs


class OwnerFileQuery(object):
    base_query = {
        "query": {
            "bool": {
                "must": []
            }
        },
        "sort": [
            {"created_date": "desc"}
        ],
        "size": 10
    }

    def __init__(self, owner, size=10):
        self._query = deepcopy(self.base_query)
        owner_term = {"match": {"owner.exact": owner}}
        self._query["query"]["bool"]["must"].append(owner_term)
        self._query["size"] = size

    def query(self):
        return self._query

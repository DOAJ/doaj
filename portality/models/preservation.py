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

    def initiated(self, owner, filename, status="initiated"):
        self.data["filename"] = filename
        self.data["owner"] = owner
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
        owner_term = {"match": {"owner": owner}}
        self._query["query"]["bool"]["must"].append(owner_term)
        self._query["size"] = size

    def query(self):
        return self._query
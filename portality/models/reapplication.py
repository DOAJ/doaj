from portality.dao import DomainObject
from datetime import datetime
from copy import deepcopy

class BulkReApplication(DomainObject):
    __type__ = 'bulk_reapplication'

    @property
    def spreadsheet_name(self):
        return self.data.get("spreadsheet_name")

    def set_spreadsheet_name(self, name):
        self.data["spreadsheet_name"] = name

    @property
    def owner(self):
        return self.data.get("owner")

    def set_owner(self, owner):
        self.data["owner"] = owner

    def created_timestamp(self):
        if "created_date" not in self.data:
            return None
        return datetime.strptime(self.data["created_date"], "%Y-%m-%dT%H:%M:%SZ")

    @classmethod
    def by_owner(cls, owner, size=10):
        q = OwnerBulkQuery(owner, size)
        res = cls.query(q=q.query())
        rs = [BulkReApplication(**r.get("_source")) for r in res.get("hits", {}).get("hits", [])]
        return rs

class BulkUpload(DomainObject):
    __type__ = "bulk_upload"

    @property
    def local_filename(self):
        return self.id + ".csv"

    @property
    def status(self):
        return self.data.get("status")

    @property
    def filename(self):
        return self.data.get("filename")

    @property
    def owner(self):
        return self.data.get("owner")

    @property
    def reapplied(self):
        return self.data.get("reapplied", 0)

    @property
    def skipped(self):
        return self.data.get("skipped", 0)

    def created_timestamp(self):
        if "created_date" not in self.data:
            return None
        return datetime.strptime(self.data["created_date"], "%Y-%m-%dT%H:%M:%SZ")

    @property
    def processed_date(self):
        return self.data.get("processed_date")

    def processed_timestamp(self):
        pd = self.processed_date
        if pd is not None:
            return datetime.strptime(pd, "%Y-%m-%dT%H:%M:%SZ")
        return None

    @property
    def error(self):
        return self.data.get("error")

    def upload(self, owner, filename, status="incoming"):
        self.data["filename"] = filename
        self.data["owner"] = owner
        self.data["status"] = status

    def failed(self, message):
        self.data["status"] = "failed"
        self.data["error"] = message
        self.data["processed_date"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

    def processed(self, reapplied, skipped):
        self.data["status"] = "processed"
        self.data["reapplied"] = reapplied
        self.data["skipped"] = skipped
        self.data["processed_date"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")


    @classmethod
    def by_owner(cls, owner, size=10):
        q = OwnerBulkQuery(owner, size)
        res = cls.query(q=q.query())
        rs = [BulkUpload(**r.get("_source")) for r in res.get("hits", {}).get("hits", [])]
        return rs

class OwnerBulkQuery(object):
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
    def __init__(self, owner, size=10):
        self._query = deepcopy(self.base_query)
        owner_term = {"term" : {"owner" : owner}}
        self._query["query"]["bool"]["must"].append(owner_term)
        self._query["size"] = size

    def query(self):
        return self._query

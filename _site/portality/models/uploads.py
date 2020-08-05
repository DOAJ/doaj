from portality.dao import DomainObject
from datetime import datetime
from copy import deepcopy

class FileUpload(DomainObject):
    __type__ = "upload"

    @property
    def status(self):
        return self.data.get("status")

    @property
    def local_filename(self):
        return self.id + ".xml"

    @property
    def filename(self):
        return self.data.get("filename")

    @property
    def schema(self):
        return self.data.get("schema")

    @property
    def owner(self):
        return self.data.get("owner")

    @property
    def imported(self):
        return self.data.get("imported", 0)

    @property
    def failed_imports(self):
        return self.data.get("failed", 0)

    @property
    def updates(self):
        return self.data.get("update", 0)

    @property
    def new(self):
        return self.data.get("new", 0)

    @property
    def error(self):
        return self.data.get("error")

    @property
    def error_details(self):
        return self.data.get("error_details")

    @property
    def failure_reasons(self):
        return self.data.get("failure_reasons", {})

    @property
    def created_timestamp(self):
        if "created_date" not in self.data:
            return None
        return datetime.strptime(self.data["created_date"], "%Y-%m-%dT%H:%M:%SZ")

    def set_schema(self, s):
        self.data["schema"] = s

    def upload(self, owner, filename, status="incoming"):
        self.data["filename"] = filename
        self.data["owner"] = owner
        self.data["status"] = status

    def failed(self, message, details=None):
        self.data["status"] = "failed"
        self.data["error"] = message
        if details is not None:
            self.data["error_details"] = details

    def validated(self, schema):
        self.data["status"] = "validated"
        self.data["schema"] = schema

    def processed(self, count, update, new):
        self.data["status"] = "processed"
        self.data["imported"] = count
        self.data["update"] = update
        self.data["new"] = new

    def partial(self, success, fail, update, new):
        self.data["status"] = "partial"
        self.data["imported"] = success
        self.data["failed"] = fail
        self.data["update"] = update
        self.data["new"] = new

    def set_failure_reasons(self, shared, unowned, unmatched):
        self.data["failure_reasons"] = {}
        if shared is not None and len(shared) > 0:
            self.data["failure_reasons"]["shared"] = shared
        if unowned is not None and len(unowned) > 0:
            self.data["failure_reasons"]["unowned"] = unowned
        if unmatched is not None and len(unmatched) > 0:
            self.data["failure_reasons"]["unmatched"] = unmatched

    def exists(self):
        self.data["status"] = "exists"

    def downloaded(self):
        self.data["status"] = "downloaded"

    @classmethod
    def list_valid(self):
        q = ValidFileQuery()
        return self.iterate(q=q.query(), page_size=10000)

    @classmethod
    def list_remote(self):
        q = ExistsFileQuery()
        return self.iterate(q=q.query(), page_size=10000)

    @classmethod
    def by_owner(self, owner, size=10):
        q = OwnerFileQuery(owner)
        res = self.query(q=q.query())
        rs = [FileUpload(**r.get("_source")) for r in res.get("hits", {}).get("hits", [])]
        return rs

class ValidFileQuery(object):
    base_query = {
        "query" : {
            "term" : { "status.exact" : "validated" }
        },
        "sort" : [
            {"created_date" : "asc"}
        ]
    }
    def __init__(self):
        self._query = deepcopy(self.base_query)

    def query(self):
        return self._query

class ExistsFileQuery(object):
    base_query = {
        "query" : {
            "term" : { "status.exact" : "exists" }
        },
        "sort" : [
            {"created_date" : "asc"}
        ]
    }
    def __init__(self):
        self._query = deepcopy(self.base_query)

    def query(self):
        return self._query

class OwnerFileQuery(object):
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
        owner_term = {"match" : {"owner" : owner}}
        self._query["query"]["bool"]["must"].append(owner_term)
        self._query["size"] = size

    def query(self):
        return self._query

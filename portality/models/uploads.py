from copy import deepcopy

from portality.dao import DomainObject, ESMappingMissingError
from portality.lib import dates


class BaseArticlesUpload(DomainObject):
    """
    Base class for article uploads. which handle status and error messages.

    This is abstract class. it has no __type__ attribute.
    For object creation and query please use FileUpload or BulkArticles instead.

    """

    @property
    def status(self):
        return self.data.get("status")

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
        return dates.parse(self.data["created_date"])

    def failed(self, message, details=None):
        self.data["status"] = "failed"
        self.data["error"] = message
        if details is not None:
            self.data["error_details"] = details

    def validated(self):
        self.data["status"] = "validated"

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

    @classmethod
    def list_valid(cls):
        q = ValidFileQuery()
        return cls.iterate(q=q.query(), page_size=10000)

    @classmethod
    def list_remote(cls):
        q = ExistsFileQuery()
        return cls.iterate(q=q.query(), page_size=10000)

    @classmethod
    def by_owner(cls, owner, size=10):
        q = OwnerFileQuery(owner)
        try:
            res = cls.query(q=q.query())
        except ESMappingMissingError:
            return []
        rs = [cls(**r.get("_source")) for r in res.get("hits", {}).get("hits", [])]
        return rs


class FileUpload(BaseArticlesUpload):
    __type__ = "upload"

    @classmethod
    def by_properties(cls, status=None, schema=None, max=10000):
        q = PropertiesQuery(status=status, schema=schema, size=max)
        return cls.object_query(q=q.query())

    @property
    def schema(self):
        return self.data.get("schema")

    def set_schema(self, s):
        self.data["schema"] = s

    @property
    def filename(self):
        return self.data.get("filename")

    @property
    def local_filename(self):
        return self.id + ".xml"

    def downloaded(self):
        self.data["status"] = "downloaded"

    def validated(self, schema=None):
        self.data["status"] = "validated"
        if schema is not None:
            self.data["schema"] = schema

    def upload(self, owner, filename, status="incoming"):
        self.data["filename"] = filename
        self.data["owner"] = owner
        self.data["status"] = status


class BulkArticles(BaseArticlesUpload):
    __type__ = "bulk_articles"

    @property
    def local_filename(self):
        return self.id + ".json"

    def incoming(self, owner):
        self.data["owner"] = owner
        self.data["status"] = "incoming"


class ValidFileQuery(object):
    base_query = {
        "track_total_hits": True,
        "query": {
            "term": {"status.exact": "validated"}
        },
        "sort": [
            {"created_date": "asc"}
        ]
    }

    def __init__(self):
        self._query = deepcopy(self.base_query)

    def query(self):
        return self._query


class ExistsFileQuery(object):
    base_query = {
        "track_total_hits": True,
        "query": {
            "term": {"status.exact": "exists"}
        },
        "sort": [
            {"created_date": "asc"}
        ]
    }

    def __init__(self):
        self._query = deepcopy(self.base_query)

    def query(self):
        return self._query


class OwnerFileQuery(object):
    base_query = {
        "track_total_hits": True,
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

class PropertiesQuery:
    def __init__(self, status=None, schema=None, size=10000):
        self._status = status
        self._schema = schema
        self._size = size

    def query(self):
        query = {
            "query": {
                "bool": {
                    "must": []
                }
            }
        }

        if self._status:
            query["query"]["bool"]["must"].append({"term": {"status.exact": self._status}})

        if self._schema:
            query["query"]["bool"]["must"].append({"term": {"schema.exact": self._schema}})

        if self._size:
            query["size"] = self._size

        return query
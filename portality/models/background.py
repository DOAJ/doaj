import datetime

from portality import dao
from portality.core import app
from portality.lib import dataobj, dates, es_data_mapping


class BackgroundJob(dataobj.DataObj, dao.DomainObject):
    """
    # ~~BackgroundJob:Model~~
    """
    __type__ = "background_job"

    def __init__(self, **kwargs):
        # FIXME: hack, to deal with ES integration layer being improperly abstracted
        if "_source" in kwargs:
            kwargs = kwargs["_source"]

        self._add_struct(BACKGROUND_STRUCT)
        if "status" not in kwargs:
            kwargs["status"] = "queued"

        # to audosave we need to move the object over to Seamless
        # self._autosave = False
        # self._audit_log_increments = 500
        # self._audit_log_counter = 0

        super(BackgroundJob, self).__init__(raw=kwargs)

    @classmethod
    def active(cls, task_type, since=None):
        # ~~-> ActiveBackgroundJob:Query~~
        q = ActiveQuery(task_type, since=since)
        actives = cls.q2obj(q=q.query())
        return actives

    def mappings(self):
        # ~~-> Elasticsearch:Technology~~
        return es_data_mapping.create_mapping(self.get_struct(), MAPPING_OPTS)

    # This feature would allow us to flush the audit logs to the index periodically.
    # We need to switch the object type to Seamless to enable that
    # def autosave(self, audit_log_increments=500):
    #     self._audit_log_increments = audit_log_increments
    #     self._autosave = True

    @property
    def user(self):
        return self._get_single("user")

    @user.setter
    def user(self, val):
        self._set_with_struct("user", val)

    @property
    def action(self):
        return self._get_single("action")

    @action.setter
    def action(self, val):
        self._set_with_struct("action", val)

    @property
    def queue_type(self):
        return self._get_single("queue_type")

    @queue_type.setter
    def queue_type(self, val):
        self._set_with_struct("queue_type", val)

    @property
    def audit(self):
        return self._get_list("audit")

    @property
    def params(self):
        return self._get_single("params")

    @params.setter
    def params(self, obj):
        self._set_single("params", obj)  # note we don't bother setting with struct, as there is none

    @property
    def reference(self):
        return self._get_single("reference")

    @reference.setter
    def reference(self, obj):
        self._set_single("reference", obj)  # note we don't bother setting with struct, as there is none

    def add_reference(self, name, value):
        if self.reference is None:
            self.reference = {}
        self.reference[name] = value

    @property
    def status(self):
        return self._get_single("status")

    def start(self):
        self._set_with_struct("status", "processing")

    def success(self):
        self._set_with_struct("status", "complete")

    def fail(self):
        self._set_with_struct("status", "error")

    def cancel(self):
        self._set_with_struct("status", "cancelled")

    def is_failed(self):
        return self._get_single("status") == "error"

    def queue(self):
        self._set_with_struct("status", "queued")

    def add_audit_message(self, msg, timestamp=None):
        if timestamp is None:
            timestamp = dates.now_with_microseconds()
        obj = {"message": msg, "timestamp": timestamp}
        self._add_to_list_with_struct("audit", obj)

        # This feature would allow us to flush the audit messages to the index periodically
        # if self._autosave:
        #     audits = len(self._get_list("audit"))
        #     if audits > self._audit_log_counter + self._audit_log_increments:
        #         self.save()
        #         self._audit_log_counter = audits

    @property
    def pretty_audit(self):
        audits = self._get_list("audit")
        return "\n".join(["{t} {m}".format(t=a["timestamp"], m=a["message"]) for a in audits])


class StdOutBackgroundJob(BackgroundJob):

    def __init__(self, inner):
        super(StdOutBackgroundJob, self).__init__(**inner.data)

    def add_audit_message(self, msg, timestamp=None):
        super(StdOutBackgroundJob, self).add_audit_message(msg, timestamp)
        if app.config.get("DOAJENV") == 'dev':
            print(msg)


# ~~-> DataObj:Library~~
BACKGROUND_STRUCT = {
    "fields": {
        "id": {"coerce": "unicode"},
        "created_date": {"coerce": "utcdatetime"},
        "last_updated": {"coerce": "utcdatetime"},
        "status": {"coerce": "unicode", "allowed_values": ["queued", "processing", "complete", "error", "cancelled"]},
        "user": {"coerce": "unicode"},
        "action": {"coerce": "unicode"},
        "queue_id": {"coerce": "unicode"},
        "es_type": {"coerce": "unicode"},
        "queue_type": {"coerce": "unicode"},
    },
    "lists": {
        "audit": {"contains": "object"}
    },
    "objects": [
        "params",  # Note that these do not have structs specified, which allows them to have arbitrary content
        "reference"
    ],
    "structs": {
        "audit": {
            "fields": {
                "message": {"coerce": "unicode"},
                "timestamp": {"coerce": "utcdatetimemicros"}
            }
        }
    }
}

# ~~-> Elasticsearch:Technology~~
MAPPING_OPTS = {
    "dynamic": None,
    "coerces": app.config["DATAOBJ_TO_MAPPING_DEFAULTS"],
    "exceptions": {
        "audit.message": {
            "type": "text",
            "index": False,
            # "include_in_all": False        # Removed in es6 fixme: do we need to look at copy_to for the mapping?
        }
    }
}


class ActiveQuery(object):
    """
    ~~ActiveBackgroundJob:Query->Elasticsearch:Technology~~
    """

    def __init__(self, task_type, size=2, since=None):
        self._task_type = task_type
        self._size = size
        self._since = since

    def query(self):
        q = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"action.exact": self._task_type}},
                        {"terms": {"status.exact": ["queued", "processing"]}}
                    ]
                }
            },
            "size": self._size
        }
        if self._since:
            q["query"]["bool"]["must"].append({"range": {"created_date": {"gte": self._since}}})
        return q


class BackgroundJobQueryBuilder:
    def __init__(self):
        self.query_dict = {
            "query": {
                "bool": {
                    "must": []
                }
            },
        }

    def append_must(self, must_dict: dict):
        self.query_dict["query"]["bool"]["must"].append(must_dict)
        return self

    def since(self, since: datetime.datetime):
        if since:
            since_str = dates.format(since)
            self.append_must({"range": {"created_date": {"gte": since_str}}})
        return self

    def action(self, action):
        self.append_must({"term": {"action.exact": action}})
        return self

    def queue_type(self, queue_type):
        self.append_must({"term": {"queue_type.exact": queue_type}})
        return self

    def status_includes(self, status):
        if isinstance(status, str):
            status = [status]
        elif not isinstance(status, list):
            status = list(status)

        self.append_must({"terms": {"status.exact": status}})
        return self

    def size(self, size: int):
        self.query_dict['size'] = size
        return self

    def order_by(self, field_name, order):
        if 'sort' not in self.query_dict:
            self.query_dict['sort'] = []

        self.query_dict['sort'].append(
            {field_name: {"order": order}}
        )
        return self

    def build_query_dict(self):
        return self.query_dict.copy()

    def build_query_object(self):
        class _Query:
            def query(subself):
                return self.build_query_dict()

        return _Query()


class SimpleBgjobQueue:
    def __init__(self, action, status, since=None):
        self.action = action
        self.status = status
        self.since = since

    def query(self):
        return (BackgroundJobQueryBuilder()
                .action(self.action)
                .since(self.since)
                .status_includes(self.status)
                .build_query_dict())


class LastCompletedJobQuery:
    def __init__(self, queue_type):
        self.queue_type = queue_type

    def query(self):
        return (BackgroundJobQueryBuilder()
                .queue_type(self.queue_type)
                .order_by('last_updated', 'desc')
                .size(1)
                .build_query_dict())


def main():
    # from portality import core
    # from portality.core import app, initialise_index
    # initialise_index(app, core.es_connection)
    # for b in BackgroundJob.active('anon_export'):
    #     print(b)

    # for b in BackgroundJob.q2obj():
    #     print(b)

    print(BackgroundJob.hit_count(ErrorQuery().query()))
    print(BackgroundJob.hit_count(ErrorQuery('reporting').query()))

    actions = {b['action'] for b in BackgroundJob.q2obj(q=ErrorQuery().query())}
    print(actions)
    # print(b['action'])


# for b in BackgroundJob.q2obj(q=ActiveQuery('sitemap').query()):
#     print(b)

# from portality.models.v1.journal import Journal
# for j in Journal.scroll(es_connection):
#     print(j)

def main2():
    query_dict = BackgroundJobQueryBuilder().status_includes('error').size(1).build_query_dict()
    for b in BackgroundJob.q2obj(q=query_dict):
        print(b)
    print(BackgroundJob.hit_count(query_dict))

    "created_date"


if __name__ == '__main__':
    main2()

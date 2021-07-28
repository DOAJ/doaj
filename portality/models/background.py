from portality.core import app
from portality.lib import dataobj, dates, es_data_mapping
from portality import dao


class BackgroundJob(dataobj.DataObj, dao.DomainObject):
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
    def has_active(cls, task_type):
        q = ActiveQuery(task_type)
        actives = cls.q2obj(q=q.query())
        return len(actives) > 0

    def mappings(self):
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
    def audit(self):
        return self._get_list("audit")

    @property
    def params(self):
        return self._get_single("params")

    @params.setter
    def params(self, obj):
        self._set_single("params", obj)     # note we don't bother setting with struct, as there is none

    @property
    def reference(self):
        return self._get_single("reference")

    @reference.setter
    def reference(self, obj):
        self._set_single("reference", obj)     # note we don't bother setting with struct, as there is none

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


BACKGROUND_STRUCT = {
    "fields": {
        "id": {"coerce": "unicode"},
        "created_date": {"coerce": "utcdatetime"},
        "last_updated": {"coerce": "utcdatetime"},
        "status": {"coerce": "unicode", "allowed_values": ["queued", "processing", "complete", "error", "cancelled"]},
        "user": {"coerce": "unicode"},
        "action": {"coerce": "unicode"},
        "queue_id": {"coerce": "unicode"},
        "es_type": {"coerce": "unicode"}
    },
    "lists": {
        "audit": {"contains": "object"}
    },
    "objects": [
        "params",           # Note that these do not have structs specified, which allows them to have arbitrary content
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

MAPPING_OPTS = {
    "dynamic": None,
    "coerces": app.config["DATAOBJ_TO_MAPPING_DEFAULTS"],
    "exceptions": {
        "audit.message": {
            "type": "string",
            "index": "not_analyzed",
            "include_in_all": False
        }
    }
}


class ActiveQuery(object):
    def __init__(self, task_type, size=1):
        self._task_type = task_type
        self._size = size

    def query(self):
        return {
            "query" : {
                "bool" : {
                    "must" : [
                        {"term" : {"action.exact" : self._task_type}},
                        {"terms" : {"status.exact" : ["queued", "processing"]}}
                    ]
                }
            },
            "size" : self._size
        }
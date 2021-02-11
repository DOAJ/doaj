from portality.lib import dataobj, dates
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

        super(BackgroundJob, self).__init__(raw=kwargs)

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


class StdOutBackgroundJob(BackgroundJob):

    def __init__(self, inner):
        super(StdOutBackgroundJob, self).__init__(**inner.data)

    def add_audit_message(self, msg, timestamp=None):
        super(StdOutBackgroundJob, self).add_audit_message(msg, timestamp)
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

from typing import Union

from portality.core import app
from portality.lib import dataobj, dates, es_data_mapping, model_utils
from portality import dao
from enum import Enum


class OutcomeStatus(Enum):
    Pending = 'pending'
    Success = 'success'
    Fail = 'fail'


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

        if not self.outcome_status:
            self.outcome_status = OutcomeStatus.Success

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

    @property
    def outcome_status(self):
        return self._get_single('outcome_status')

    def outcome_fail(self):
        self.outcome_status = OutcomeStatus.Fail

    @outcome_status.setter
    def outcome_status(self, outcome_status: Union[str, OutcomeStatus]):
        if isinstance(outcome_status, OutcomeStatus):
            outcome_status = outcome_status.value
        self._set_with_struct('outcome_status', outcome_status)

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

        # status of bgjob level, for example, This job experienced an exception and failed to complete normally
        "status": {"coerce": "unicode", "allowed_values": ["queued", "processing", "complete", "error", "cancelled"]},
        "user": {"coerce": "unicode"},
        "action": {"coerce": "unicode"},
        "queue_id": {"coerce": "unicode"},
        "es_type": {"coerce": "unicode"},

        # status of bgjob result (business logic level), for example, The job completed without exception,
        # but the action the user wanted was not carried out for some reason
        "outcome_status": {"coerce": "unicode"} | model_utils.create_allowed_values_by_enum(OutcomeStatus),
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
        if self._since:
            q["query"]["bool"]["must"].append({"range" : {"created_date" : {"gte":  self._since}}})
        return q
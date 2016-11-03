from portality.lib import dataobj, dates
from portality import dao

class BackgroundJob(dataobj.DataObj, dao.DomainObject):
    __type__ = "background_job"

    def __init__(self, **kwargs):
        # FIXME: hack, to deal with ES integration layer being improperly abstracted
        if "_source" in kwargs:
            kwargs = kwargs["_source"]

        self._add_struct(BACKGROUND_STRUCT)
        super(BackgroundJob, self).__init__(raw=kwargs)

    @property
    def user(self):
        return self._get_single("user")

    @property
    def audit(self):
        return self._get_list("audit")

    def add_audit_message(self, msg, timestamp=None):
        if timestamp is None:
            timestamp = dates.now()
        obj = {"message" : msg, "timestamp": timestamp}
        self._add_to_list_with_struct("audit", obj)


BACKGROUND_STRUCT = {
    "fields" : {
        "id" :{"coerce" : "unicode"},
        "created_date" : {"coerce" : "utcdatetime"},
        "last_updated" : {"coerce" : "utcdatetime"},
        "status" : {"coerce" : "unicode", "allowed_values" : [u"queued", u"processing", u"complete", u"error"]},
        "user" : {"coerce" : "unicode"},
        "action" : {"coerce" : "unicode"},
        "queue_id" : {"coerce" : "unicode"}
    },
    "lists" : {
        "audit" : {"contains" : "object"}
    },
    "objects" : [
        "params",           # Note that these do not have structs specified, which allows them to have arbitrary content
        "reference"
    ],
    "structs" : {
        "audit" : {
            "fields" : {
                "message" : {"coerce" : "unicode"},
                "timestamp" : {"coerce" : "utcdatetime"}
            }
        }
    }
}
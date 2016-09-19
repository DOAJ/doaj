from portality.dao import DomainObject
from portality.lib import dataobj

class Provenance(dataobj.DataObj, DomainObject):
    """
    {
        "id" : "<provenance record id>",
        "created_date" : "<when this action took place>",
        "user": "<user that carried out the action>",
        "editor_group": ["<list of editor groups the user was in at the time>"],
        "type" : "<type being acted on: suggestion, journal, etc>",
        "subtype" : "<inner type being acted on, in case you want to distinguish between applications/reapplications, etc>",
        "action" : "<string denoting the action taken on the object>",
        "resource_id" : "<id of the type being acted on>"
    }
    """

    __type__ = "provenance"

    def __init__(self, **kwargs):
        # FIXME: hack, to deal with ES integration layer being improperly abstracted
        if "_source" in kwargs:
            kwargs = kwargs["_source"]
        self._add_struct(PROVENANCE_STRUCT)
        super(Provenance, self).__init__(raw=kwargs)

    @property
    def type(self):
        return self._get_single("type")

    @type.setter
    def type(self, val):
        self._set_with_struct("type", val)

    def save(self, **kwargs):
        # self.prep()
        self.check_construct()
        super(Provenance, self).save(**kwargs)


PROVENANCE_STRUCT = {
    "fields" : {
        "id" : {"coerce" : "unicode"},
        "created_date" : {"coerce" : "utcdatetime"},
        "user" : {"coerce" : "unicode"},
        "type" : {"coerce" : "unicode"},
        "subtype" : {"coerce" : "unicode"},
        "action" : {"coerce" : "unicode"},
        "resource_id" : {"coerce" : "unicode"}
    },
    "lists" : {
        "editor_group" : {"contains" : "field", "coerce" : "unicode"}
    }
}
from portality.dao import DomainObject
from portality.lib import dataobj
from portality.models import EditorGroup

class Provenance(dataobj.DataObj, DomainObject):
    """
    {
        "id" : "<provenance record id>",
        "created_date" : "<when this action took place>",
        "last_updated" : "<when this record was last updated>",
        "user": "<user that carried out the action>",
        "roles" : ["<roles this user has at the time of the event>"],
        "editor_group": ["<list of editor groups the user was in at the time>"],
        "type" : "<type being acted on: suggestion, journal, etc>",
        "subtype" : "<inner type being acted on, in case you want to distinguish between applications/update requests, etc>",
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

    @property
    def user(self):
        return self._get_single("user")

    @user.setter
    def user(self, val):
        self._set_with_struct("user", val)

    @property
    def roles(self):
        return self._get_list("roles")

    @roles.setter
    def roles(self, val):
        self._set_with_struct("roles", val)

    @property
    def editor_group(self):
        return self._get_list("editor_group")

    @property
    def subtype(self):
        return self._get_single("subtype")

    @property
    def action(self):
        return self._get_single("action")

    @action.setter
    def action(self, val):
        self._set_with_struct("action", val)

    @property
    def resource_id(self):
        return self._get_single("resource_id")

    @resource_id.setter
    def resource_id(self, val):
        self._set_with_struct("resource_id", val)

    def save(self, **kwargs):
        # self.prep()
        self.check_construct()
        return super(Provenance, self).save(**kwargs)

    @classmethod
    def make(cls, account, action, obj, subtype=None, save=True):
        egs1 = EditorGroup.groups_by_editor(account.id)
        egs2 = EditorGroup.groups_by_associate(account.id)
        egs = []
        for eg in egs1:
            if eg.id not in egs:
                egs.append(eg.id)
        for eg in egs2:
            if eg.id not in egs:
                egs.append(eg.id)

        d = {
            "user" : account.id,
            "roles" : account.role,
            "type" : obj.__type__,
            "action" : action,
            "resource_id" : obj.id,
            "editor_group" : egs
        }
        if subtype is not None:
            d["subtype"] = subtype

        p = Provenance(**d)
        if save:
            saved = p.save()
            if saved is None:
                raise ProvenanceException("Failed to save provenance record")
        return p

    @classmethod
    def get_latest_by_resource_id(cls, resource_id):
        q = ResourceIDQuery(resource_id)
        resp = cls.query(q=q.query())
        obs = [hit.get("_source") for hit in resp.get("hits", {}).get("hits", [])]
        if len(obs) == 0:
            return None
        return Provenance(**obs[0])


PROVENANCE_STRUCT = {
    "fields" : {
        "id" : {"coerce" : "unicode"},
        "created_date" : {"coerce" : "utcdatetime"},
        "last_updated" : {"coerce" : "utcdatetime"},
        "user" : {"coerce" : "unicode"},
        "type" : {"coerce" : "unicode"},
        "subtype" : {"coerce" : "unicode"},
        "action" : {"coerce" : "unicode"},
        "resource_id" : {"coerce" : "unicode"}
    },
    "lists" : {
        "roles" : {"contains" : "field", "coerce" : "str"},
        "editor_group" : {"contains" : "field", "coerce" : "str"}
    }
}

class ResourceIDQuery(object):
    def __init__(self, resource_id):
        self.resource_id = resource_id

    def query(self):
        return {
            "query" : {
                "bool" : {
                    "must" : [
                        {"term" : {"resource_id.exact" : self.resource_id}}
                    ]
                }
            },
            "sort" : [{"created_date" : {"order" : "desc"}}]
        }

class ProvenanceException(Exception):
    pass
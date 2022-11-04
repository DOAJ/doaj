from portality.dao import DomainObject, ScrollInitialiseException
from portality.models import Account


class EditorGroup(DomainObject):
    """
    ~~EditorGroup:Model~~
    """
    __type__ = "editor_group"

    @classmethod
    def group_exists_by_name(cls, name):
        q = EditorGroupQuery(name)
        res = cls.query(q=q.query())
        ids = [hit.get("_source", {}).get("id") for hit in res.get("hits", {}).get("hits", []) if "_source" in hit]
        if len(ids) == 0:
            return None
        if len(ids) > 0:
            return ids[0]

    @classmethod
    def _groups_by_x(cls, **kwargs):
        """ Generalised editor groups by maned / editor / associate """
        # ~~-> EditorGroupMember:Query~~
        q = EditorGroupMemberQuery(**kwargs)
        try:
            return [g for g in cls.iterate(q.query(), page_size=100)]
        except ScrollInitialiseException:
            # If there's no mapping for editor groups, the account definitely has no assignments.
            return []

    @classmethod
    def groups_by_maned(cls, maned):
        return cls._groups_by_x(maned=maned)

    @classmethod
    def groups_by_editor(cls, editor):
        return cls._groups_by_x(editor=editor)

    @classmethod
    def groups_by_associate(cls, associate):
        return cls._groups_by_x(associate=associate)

    @property
    def name(self):
        return self.data.get("name")

    def set_name(self, val):
        self.data["name"] = val

    @property
    def maned(self):
        return self.data.get("maned")

    def set_maned(self, val):
        self.data["maned"] = val

    def get_maned_account(self):
        return Account.pull(self.maned)

    @property
    def editor(self):
        return self.data.get("editor")

    def set_editor(self, val):
        self.data["editor"] = val

    def get_editor_account(self):
        return Account.pull(self.editor)

    @property
    def associates(self):
        return self.data.get("associates", [])

    def set_associates(self, val):
        if not isinstance(val, list):
            val = [val]
        self.data["associates"] = val

    def add_associate(self, val):
        if "associates" not in self.data:
            self.data["associates"] = []
        self.data["associates"].append(val)

    def get_associate_accounts(self):
        accs = []
        for a in self.associates:
            acc = Account.pull(a)
            accs.append(acc)
        return accs

    def is_member(self, account_name):
        """ Determine if an account is a member of this Editor Group """
        all_eds = self.associates + [self.editor]
        return account_name in all_eds


class EditorGroupQuery(object):
    def __init__(self, name):
        self.name = name

    def query(self):
        q = {
            "track_total_hits" : True,
            "query": {"term": {"name.exact": self.name}}
        }
        return q


class EditorGroupMemberQuery(object):
    """
    ~~EditorGroupMember:Query->Elasticsearch:Technology~~
    """
    def __init__(self, editor=None, associate=None, maned=None):
        self.editor = editor
        self.associate = associate
        self.maned = maned

    def query(self):
        q = {
            "track_total_hits": True,
            "query": {"bool": {"should": []}},
            "sort": {"name.exact": {"order" : "asc"}}
        }
        if self.editor is not None:
            et = {"term": {"editor.exact": self.editor}}
            q["query"]["bool"]["should"].append(et)
        if self.associate is not None:
            at = {"term": {"associates.exact": self.associate}}
            q["query"]["bool"]["should"].append(at)
        if self.maned is not None:
            mt = {"term" : {"maned.exact" : self.maned}}
            q["query"]["bool"]["should"].append(mt)
        return q

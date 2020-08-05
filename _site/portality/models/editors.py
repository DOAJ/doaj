from portality.dao import DomainObject
from portality.models import Account

class EditorGroup(DomainObject):
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
    def groups_by_editor(cls, editor):
        q = EditorGroupMemberQuery(editor=editor)
        iter = cls.iterate(q.query(), page_size=100)
        return iter

    @classmethod
    def groups_by_associate(cls, associate):
        q = EditorGroupMemberQuery(associate=associate)
        iter = cls.iterate(q.query(), page_size=100)
        return iter

    @property
    def name(self):
        return self.data.get("name")

    def set_name(self, val):
        self.data["name"] = val

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

class EditorGroupQuery(object):
    def __init__(self, name):
        self.name = name
    def query(self):
        q = {"query" : {"term" : {"name.exact" : self.name}}}
        return q

class EditorGroupMemberQuery(object):
    def __init__(self, editor=None, associate=None):
        self.editor = editor
        self.associate = associate

    def query(self):
        q = {"query" : {"bool" : {"should" : []}}}
        if self.editor is not None:
            et = {"term" : {"editor.exact" : self.editor}}
            q["query"]["bool"]["should"].append(et)
        if self.associate is not None:
            at = {"term" : {"associates.exact" : self.associate}}
            q["query"]["bool"]["should"].append(at)
        return q

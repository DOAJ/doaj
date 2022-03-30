from portality.lib import dates
import json


class Event(object):
    def __init__(self, id=None, who=None, context=None, raw=None):
        if raw is not None:
            self.data = raw
        else:
            self.data = {
                "when" : dates.now()
            }
            if id is not None:
                self.id = id
            if who is not None:
                self.who = who
            if context:
                self.set_context(**context)

    @property
    def id(self):
        return self.data.get("id")

    @id.setter
    def id(self, val):
        self.data["id"] = val

    @property
    def who(self):
        return self.data.get("who")

    @who.setter
    def who(self, val):
        self.data["who"] = val

    @property
    def context(self):
        return self.data.get("context")

    def set_context(self, **kwargs):
        self.data["context"] = kwargs

    def serialise(self):
        return json.dumps(self.data)

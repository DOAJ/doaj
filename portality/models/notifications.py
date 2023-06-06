from portality.dao import DomainObject
from portality.lib import dates


class Notification(DomainObject):
    """~~Notification:Model->DomainObject:Model~~"""
    __type__ = "notification"

    def __init__(self, **kwargs):
        super(Notification, self).__init__(**kwargs)

    @property
    def who(self):
        return self.data.get("who")

    @who.setter
    def who(self, account_id):
        self.data["who"] = account_id

    @property
    def short(self):
        return self.data.get("short")

    @short.setter
    def short(self, message):
        self.data["short"] = message

    @property
    def long(self):
        return self.data.get("long")

    @long.setter
    def long(self, message):
        self.data["long"] = message

    @property
    def seen_date(self):
        return self.data.get("seen_date")

    @seen_date.setter
    def seen_date(self, date):
        self.data["seen_date"] = date

    def is_seen(self):
        return "seen_date" in self.data

    def set_seen(self):
        self.seen_date = dates.now_str()

    @property
    def action(self):
        return self.data.get("action")

    @action.setter
    def action(self, action_url):
        self.data["action"] = action_url

    @property
    def classification(self):
        return self.data.get("classification")

    @classification.setter
    def classification(self, classification):
        self.data["classification"] = classification

    @property
    def created_by(self):
        return self.data.get("created_by")

    @created_by.setter
    def created_by(self, consumer_id):
        self.data["created_by"] = consumer_id


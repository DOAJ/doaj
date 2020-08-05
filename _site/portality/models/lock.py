from portality.dao import DomainObject
from datetime import datetime, timedelta
import tzlocal

class Lock(DomainObject):
    __type__ = "lock"
    """
    {
        "id" : "<opaque id for this lock>",
        "about" : "<opaque id for the journal/suggestion to which it applies>",
        "type" : "<journal/suggestion>",
        "created_date" : "<timestamp this lock record was created>",
        "expires" : "<timestamp for when this lock record expires>",
        "username" : "<user name of the user who holds the lock>"
    }
    """
    @property
    def about(self):
        return self.data.get("about")

    def set_about(self, val):
        self.data["about"] = val

    @property
    def type(self):
        return self.data.get("type")

    def set_type(self, val):
        if val not in ["journal", "suggestion"]:
            return
        self.data["type"] = val

    @property
    def username(self):
        return self.data.get("username")

    def set_username(self, val):
        self.data["username"] = val

    @property
    def expires(self):
        return self.data.get('expires')

    def expires_in(self, timeout):
        expires = datetime.now() + timedelta(0, timeout)
        self.data["expires"] = expires.strftime("%Y-%m-%dT%H:%M:%SZ")

    def is_expired(self):
        ed = datetime.strptime(self.expires, "%Y-%m-%dT%H:%M:%SZ")
        return ed <= datetime.now()

    def utc_expires(self):
        ed = datetime.strptime(self.expires, "%Y-%m-%dT%H:%M:%SZ")
        local = tzlocal.get_localzone()
        ld = local.localize(ed)
        tt = ld.utctimetuple()
        utcdt = datetime(tt.tm_year, tt.tm_mon, tt.tm_mday, tt.tm_hour, tt.tm_min, tt.tm_sec)
        return utcdt.strftime("%Y-%m-%dT%H:%M:%SZ")

    def expire_formatted(self, format="%H:%M"):
        ed = datetime.strptime(self.expires, "%Y-%m-%dT%H:%M:%SZ")
        formatted = ed.strftime(format)
        return formatted

    def would_expire_within(self, timeout):
        limit = datetime.now() + timedelta(0, timeout)
        ed = datetime.strptime(self.expires, "%Y-%m-%dT%H:%M:%SZ")
        return ed < limit

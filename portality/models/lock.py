from portality.dao import DomainObject
from datetime import datetime, timedelta
import tzlocal

from portality.lib import dates
from portality.lib.dates import FMT_DATETIME_STD


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
        expires = dates.now() + timedelta(0, timeout)
        self.data["expires"] = expires.strftime(FMT_DATETIME_STD)

    def is_expired(self):
        ed = dates.parse(self.expires)
        return ed <= dates.now()

    def utc_expires(self):
        ed = dates.parse(self.expires)
        local = tzlocal.get_localzone()
        ld = local.localize(ed)
        tt = ld.utctimetuple()
        utcdt = datetime(tt.tm_year, tt.tm_mon, tt.tm_mday, tt.tm_hour, tt.tm_min, tt.tm_sec)
        return utcdt.strftime(FMT_DATETIME_STD)

    def expire_formatted(self, format="%H:%M"):
        ed = dates.parse(self.expires)
        formatted = ed.strftime(format)
        return formatted

    def would_expire_within(self, timeout):
        limit = dates.now() + timedelta(0, timeout)
        ed = dates.parse(self.expires)
        return ed < limit

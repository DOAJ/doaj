from portality import models
from portality.core import app

class Locked(Exception):
    def __init__(self, message, lock):
        self.message = message
        self.lock = lock

def lock(type, id, username):
    """
    Obtain a lock on the object for the given username.  If unable to obtain
    a lock, raise an exception
    """
    l = models.Lock.pull_by_key("about", id)

    if l is None:
        print "no lock"
        l = models.Lock()
        l.set_about(id)
        l.set_type(type)
        l.set_username(username)
        l.expires_in(app.config.get("EDIT_LOCK_TIMEOUT", 1200))
        l.save()
        return l

    indate = not l.is_expired()
    yours = l.username == username

    print "in date", indate, "yours", yours

    if not yours and not indate:
        # overwrite the old lock with a new one
        l.set_username(username)
        l.expires_in(app.config.get("EDIT_LOCK_TIMEOUT", 1200))
        l.save()
        return l

    if not yours and indate:
        # someone else holds the lock, so raise exception
        raise Locked("Object is locked by another user", l)

    if yours:
        # the lock is yours so we extend it, whether it is in date or not
        l.expires_in(app.config.get("EDIT_LOCK_TIMEOUT", 1200))
        l.save()
        return l

    # shouldn't ever get here - if we do something is bust
    raise Locked("Unable to resolve lock state", None)

def unlock(type, id, username):
    l = models.Lock.pull_by_key("about", id)
    if l.username == username:
        l.delete()
        return True
    return False
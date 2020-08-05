from portality import models
from portality.core import app
from portality.dao import ESMappingMissingError

class Locked(Exception):
    def __init__(self, message, lock):
        self.message = message
        self.lock = lock

def lock(type, id, username, timeout=None, blocking=False):
    """
    Obtain a lock on the object for the given username.  If unable to obtain
    a lock, raise an exception
    """
    if timeout is None:
        timeout = app.config.get("EDIT_LOCK_TIMEOUT", 1200)

    l = _retrieve_latest_with_cleanup(type, id)

    if l is None:
        l = models.Lock()
        l.set_about(id)
        l.set_type(type)
        l.set_username(username)
        l.expires_in(timeout)
        l.save(blocking=blocking)
        return l

    indate = not l.is_expired()
    yours = l.username == username

    if not yours and not indate:
        # overwrite the old lock with a new one
        l.set_username(username)
        l.expires_in(timeout)
        l.save(blocking=blocking)
        return l

    if not yours and indate:
        # someone else holds the lock, so raise exception
        raise Locked("Object is locked by another user", l)

    if yours:
        # if the lock would expire within the time specified by the timeout, extend it
        if l.would_expire_within(timeout):
            l.expires_in(timeout)
            l.save(blocking=blocking)
        return l

    # shouldn't ever get here - if we do something is bust
    raise Locked("Unable to resolve lock state", None)

def unlock(type, id, username):
    l = _retrieve_latest_with_cleanup(type, id)

    if l is None:
        return True

    if l.username == username:
        l.delete()
        return True

    return False

def has_lock(type, id, username):
    l = _retrieve_latest_with_cleanup(type, id)

    if l is None:
        return False

    indate = not l.is_expired()
    yours = l.username == username

    if indate and yours:
        return True

    return False

def batch_lock(type, ids, username, timeout=None):
    """
    Batch lock succeeds and fails as a unit.  If locks can't be obtained on everything
    then all locks are released.

    Works by attempting to lock everything, and then backing out, unlocking already locked
    resources, when it first encounters a locked record

    :param type:
    :param ids:
    :param username:
    :return:
    """
    locked = []
    locks = []
    abort = False
    failon = None
    for id in ids:
        try:
            lock(type, id, username, timeout)
            locked.append(id)
            locks.append(lock)
        except Locked as e:
            abort = True
            failon = id
            break

    if abort:
        for id in locked:
            unlock(type, id, username)
        raise Locked("Batch lock failed on id {x}".format(x=failon), None)

    return locks

def batch_unlock(type, ids, username):
    """
    Calls unlock on all resources.  Unlock may fail on one or more resources
    without affecting the others.

    :param type:
    :param ids:
    :param username:
    :return:
    """
    success = []
    fail = []
    for id in ids:
        unlocked = unlock(type, id, username)
        if unlocked:
            success.append(id)
        else:
            fail.append(id)

    return {"success": success, "fail" : fail}

def _retrieve_latest_with_cleanup(type, id):
    # query for any locks on this id.  There is a chance there's more than one, if two locks
    # are created at the same time
    l = None

    q = LockQuery(type, id)
    try:
        ls = models.Lock.q2obj(q=q.query())
    except ESMappingMissingError:
        return l

    # if there's more than one lock, keep the most recent (the query is sorted) and
    # delete all the rest.  Code that uses locks should check for a lock before each
    # operation, and handle the fact that it may lose its lock.
    if len(ls) > 0:
        l = ls[0]
    if len(ls) > 1:
        for i in range(1, len(ls)):
            ls[i].delete()

    return l

class LockQuery(object):
    def __init__(self, type, about):
        self.about = about
        self.type = type

    def query(self):
        return {
            "query" : {
                "bool" : {
                    "must" : [
                        {"term" : {"about.exact" : self.about}},
                        {"term" : {"type.exact" : self.type}}
                    ]
                }
            },
            "sort" : [{"last_updated" : {"order" : "desc"}}]
        }
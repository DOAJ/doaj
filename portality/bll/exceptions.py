import sys, traceback, json

class AuthoriseException(Exception):
    """
    Exception to raise if an action is not authorised
    ~~AuthNZ:Exception->AuthNZ:Feature~~
    """

    # standardised reasons why an action might not be allowed
    NOT_OWNER = "not_owner"
    WRONG_ROLE = "wrong_role"
    WRONG_STATUS = "wrong_status"
    NOT_AUTHORISED = "not_authorised"

    def __init__(self, message=None, reason=None):
        super(AuthoriseException, self).__init__(message)
        self.reason = reason

class NoSuchFormContext(Exception):
    """
    Exception to raise if a form context is requested that can't be found
    """
    pass

class ArgumentException(Exception):
    """
    Exception to raise if an expected argument is not present
    """
    pass

class SaveException(Exception):
    """
    Exception to raise if a save operation did not work as expected
    """
    pass

class NoSuchObjectException(Exception):
    """
    Exception to raise if the object id given does not correspond to an actual object
    in the datastore
    """
    pass

class NoSuchPropertyException(Exception):
    """
    Exception to raise if an object does not have a property that was required of it
    to complete the operation
    """
    pass

class ConfigurationException(Exception):
    """
    Exception to raise when our own configuration is broken
    """
    pass

class DuplicateArticleException(Exception):
    """
    Exception to raise when a duplicate article is detected, and this is not permitted
    """
    pass

class ArticleNotAcceptable(Exception):
    """
    Exception to raise when an article does not have suitable data to be ingested into DOAJ
    """
    def __init__(self, *args, **kwargs):
        self.message = kwargs.get("message", "")
        self.result = kwargs.get("result", {})
        super(ArticleNotAcceptable, self).__init__(*args)

    def __str__(self):
        super(ArticleNotAcceptable, self).__str__()
        return self.message

class ArticleMergeConflict(Exception):
    """
    Exception to raise when it's not clear which article to merge an update with
    """
    pass

class IllegalStatusException(Exception):
    """
    Exception to raise when an application is in a state that is not allowed for the current action
    """

    def __init__(self, message=None):
        super(IllegalStatusException, self).__init__(message)

class DuplicateUpdateRequest(Exception):
    """
    Exception to raise when an attempt is made to create mulitple or duplicate update requests for a journal
    """

    def __init__(self, message=None):
        super(DuplicateUpdateRequest, self).__init__(message)


class IngestException(Exception):
    """
    ~~ArticleIngest:Exception->Article:Service~~
    """
    def __init__(self, *args, **kwargs):
        self.stack = None
        self.message = kwargs.get("message")
        self.inner_message = kwargs.get("inner_message")
        self.inner = kwargs.get("inner")
        self.result = kwargs.get("result", {})

        tb = sys.exc_info()[2]
        if self.inner is not None:
            if self.inner_message is None and self.inner.args[0] is not None:
                self.inner_message = self.inner.args[0]

            if tb is not None:
                self.stack = "".join(traceback.format_exception(self.inner.__class__, self.inner, tb))
            else:
                self.stack = "".join(traceback.format_exception_only(self.inner.__class__, self.inner))
        else:
            if tb is not None:
                self.stack = "".join(traceback.format_tb(tb))
            else:
                self.stack = "".join(traceback.format_stack())

    def trace(self):
        return self.stack

    def __str__(self):
        repr = "Ingest Exception: "
        if self.message:
            repr += self.message
        if self.inner_message:
            repr += " - " + self.inner_message
        if self.result:
            repr += " (" + json.dumps(self.result, cls=SetEncoder) + ")"
        return repr


class SetEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return json.JSONEncoder.default(self, obj)
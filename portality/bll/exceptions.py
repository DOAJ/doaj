import sys, traceback

class AuthoriseException(Exception):
    """
    Exception to raise if an action is not authorised
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
        self.errors = kwargs.get("errors", [])
        super(ArticleNotAcceptable, self).__init__(*args)

class ArticleMergeConflict(Exception):
    """
    Exception to raise when it's not clear which article to merge an update with
    """
    pass

class ArticleExists(Exception):
    def __init__(self, article_id):
        self.article_id = article_id
    """
    Exception to raise when the update is going to override another article
    """

class IngestException(Exception):
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
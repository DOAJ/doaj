

class ArticleFromWithdrawnJournal(Exception):
    """
        Raised when when an attempt is made to access an article that appears in withdrawn journal
    """

    def __init__(self, message=None, **kwargs):
        super(ArticleFromWithdrawnJournal, self).__init__(message)


class TombstoneArticle(Exception):
    """
        Raised when when an attempt is made to access an article that has been deleted
    """

    def __init__(self, message=None, **kwargs):
        super(TombstoneArticle, self).__init__(message)


class JournalWithdrawn(Exception):
    """
        Raised when an attempt is made to access a withdrawn journal.
    """

    def __init__(self, message=None, context=None):
        super(JournalWithdrawn, self).__init__(message)

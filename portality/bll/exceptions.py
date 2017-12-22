class AuthoriseException(Exception):
    """
    Exception to raise if an action is not authorised
    """

    # standardised reasons why an action might not be allowed
    NOT_OWNER = "not_owner"
    WRONG_ROLE = "wrong_role"
    WRONG_STATUS = "wrong_status"

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
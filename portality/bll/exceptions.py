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
from portality.bll.exceptions import IngestException

class CrosswalkException(IngestException):
    """
    Exception to raise if there's a problem with the content being passed to the crosswalk
    """
    pass
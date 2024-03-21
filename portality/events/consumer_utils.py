from portality import models
from portality.bll import exceptions


def parse_application(application_raw: dict) -> models.Application:
    try:
        return models.Application(**application_raw)
    except Exception as e:
        raise exceptions.NoSuchObjectException(
            "Unable to construct Application from supplied source - data structure validation error, {x}".format(x=e)
        )

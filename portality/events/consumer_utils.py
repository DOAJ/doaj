from portality import models
from portality.bll import exceptions
from portality.core import app


def parse_application(application_raw: dict) -> models.Application:
    try:
        return models.Application(**application_raw)
    except Exception as e:
        raise exceptions.NoSuchObjectException(
            "Unable to construct Application from supplied source - data structure validation error, {x}".format(x=e)
        )


def is_enable_publisher_email() -> bool:
    # TODO: in the long run this needs to move out to the user's email preferences but for now it
    # is here to replicate the behaviour in the code it replaces
    return app.config.get("ENABLE_PUBLISHER_EMAIL", False)

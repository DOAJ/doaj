from portality.constants import EXPARAM_EDITING_USER


def exparam_editing_user() -> dict:
    """
    Create extra params -- editing_user
    :return:
    """

    from flask_login import current_user
    return {
        EXPARAM_EDITING_USER: current_user,
    }

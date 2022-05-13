from portality import constants


def make_update_request(application):
    if application.related_journal and not application.application_type == constants.APPLICATION_TYPE_UPDATE_REQUEST:
        application.application_type = constants.APPLICATION_TYPE_UPDATE_REQUEST
    return application


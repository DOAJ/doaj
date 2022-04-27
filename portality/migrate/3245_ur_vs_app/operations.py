from portality import constants
def make_update_request(application):
    if application.related_journal:
        application.application_type = constants.APPLICATION_TYPE_UPDATE_REQUEST
        application.save()
    return application


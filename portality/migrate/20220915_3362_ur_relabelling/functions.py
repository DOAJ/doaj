from portality import constants
from portality.models import Journal


def detect_application_type(application):
    # for all applications with a current journal, tag them as an update request
    if application.current_journal is not None:
        application.set_is_update_request(True)
        return application

    # for all applications with no current journal and no related journal, tag them as a new application
    if application.related_journal is None:
        application.set_is_update_request(False)
        return application

    # An application with a related journal which has been rejected is an UR, as a new application
    # would not have a related journal field
    if application.application_status == constants.APPLICATION_STATUS_REJECTED:
        application.set_is_update_request(True)
        return application

    # Applications matching rules below here are:
    # * missing a current_journal
    # * with a related_journal field
    # * NOT rejected

    # All the next migration rules require us to know about the other related applications

    # If we can't find a related journal, set this as a new application, because we can't tell otherwise
    journal = Journal.pull(application.related_journal)
    if journal is None:
        if application.application_status != constants.APPLICATION_STATUS_REJECTED:
            print("missing related journal {x} for application {y}".format(x=application.related_journal, y=application.id))
        application.set_is_update_request(False)
        return application

    relaps = journal.related_applications
    current_application = journal.current_application

    # if there is no reciprocal relationship, we may need to fix the data, depending on other
    # circumstances
    if len(relaps) == 0:
        if application.application_status == constants.APPLICATION_STATUS_ACCEPTED:
            # the relationship is broken and we should fix it
            # we take this as a single missing relationship, which means this is a new application
            journal.add_related_application(application.id)
            print("fixed missing reciprocal relationship application {x} for journal {y}".format(x=application.id, y=journal.id))

            # do a check to make sure the accepted application is not still a current_application
            if current_application == application.id:
                print("fixed erroneous current_application for new application {x} for journal {y}".format(x=application.id, y=journal.id))
                journal.remove_current_application()

            journal.save()

            # if the application is accepted, and the journal does not list any related applications we assume this is
            # a new application, as there is no other data to go on
            application.set_is_update_request(False)
            return application

        else:
            # At this point the application is not in the accepted or rejected status

            # if the journal lists a current application and it is not this application, then everything is a mess and
            # we would probably need to look at this manually
            if current_application is not None and current_application != application.id:
                print("illegal state", application.id)

            # if the journal exists, and a non-accepted application for it exists, then it is an
            # update request
            application.set_is_update_request(True)
            return application

    # for all applications which have a related journal for which they are
    # the only application, tag them as a new application
    if len(relaps) == 1:
        application.set_is_update_request(False)
        return application

    # The next bit requires us to know about the applications in order
    sorted(relaps, key=lambda x: x.get("date_accepted", "1970-01-01T00:00:00Z"))

    # for all applications which have a related journal, and of all other applications
    # for that journal they have the earliest created_date (they are the oldest), tag them as a new application
    if relaps[-1].get("application_id") == application.id:
        application.set_is_update_request(False)
        return application

    # for all applications which have a related journal, and of all the other applications for that
    # journal they DO NOT have the earliest created_date, tag them as an update request
    application.set_is_update_request(True)
    return application
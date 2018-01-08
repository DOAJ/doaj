def clear_current_journal(application):
    if application.application_status in ["rejected", "accepted"]:
        cj = application.current_journal
        if cj is not None:
            application.remove_current_journal()
            application.set_related_journal(cj)
    return application

def relabel_status(application):
    if application.application_status == "reapplication":
        application.set_application_status("update_request")
    return application
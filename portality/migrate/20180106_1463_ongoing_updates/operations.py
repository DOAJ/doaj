def clear_current_journal(application):
    if application.application_status in ["rejected", "accepted"]:
        application.remove_current_journal()
    return application

def relabel_status(application):
    if application.application_status == "reapplication":
        application.set_application_status("update_request")
    return application
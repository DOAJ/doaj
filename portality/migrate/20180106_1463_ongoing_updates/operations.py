def clear_current_journal(application):
    if application.application_status in ["rejected", "accepted"]:
        application.remove_current_journal()
    return application
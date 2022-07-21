from portality.models import Event
from portality.bll import DOAJ
from portality import constants
from portality.app import app

with app.test_request_context("/"):
    svc = DOAJ.eventsService()
    svc.trigger(Event(constants.EVENT_APPLICATION_STATUS, "richard",
                      context={"old_status" : "ready", "new_status" : "in progress", "application": "115e2ab11a644599a66f73dee9626fcd"}))
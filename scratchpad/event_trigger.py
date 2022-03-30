from portality.models import Event
from portality.bll import DOAJ
from portality import constants
from portality.app import app

with app.test_request_context("/"):
    svc = DOAJ.eventsService()
    svc.trigger(Event(constants.EVENT_ACCOUNT_CREATED, context={"account" : "richard"}))
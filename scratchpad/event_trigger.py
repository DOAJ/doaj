from portality.models import Event
from portality.bll import DOAJ
from portality import constants

svc = DOAJ.eventsService()
svc.trigger(Event(constants.EVENT_ACCOUNT_CREATED, account="richard"))
from portality.bll import DOAJ
from portality import util

event_logger = util.custom_timed_rotating_logger('shortcircuit_log.log')

def send_event(event):
    event_logger.info(event.data)
    svc = DOAJ.eventsService()
    svc.consume(event)
from portality.bll import DOAJ


def send_event(event):
    svc = DOAJ.eventsService()
    svc.consume(event)
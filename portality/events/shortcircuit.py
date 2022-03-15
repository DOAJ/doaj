from portality.bll import DOAJ

svc = DOAJ.eventsService()


def send_event(event):
    svc.consume(event)
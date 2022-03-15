from portality.core import app
from portality.lib import plugin

from portality.events.consumers.account_created_email import AccountCreatedEmail

EVENT_CONSUMERS = [
    AccountCreatedEmail()
]

class EventsService(object):
    def __init__(self):
        self.trigger_function = plugin.load_function(app.config.get("EVENT_SEND_FUNCTION"))

    def trigger(self, event):
        self.trigger_function(event)

    def consume(self, event):
        for consumer in EVENT_CONSUMERS:
            if consumer.consumes(event):
                consumer.consume(event)
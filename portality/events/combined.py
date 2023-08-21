from portality.events.shortcircuit import send_event as shortcircuit_send_event
from portality.core import app


def send_event(event):
    try:
        from portality.events.kafka_producer import send_event as kafka_send_event
        kafka_send_event(event)
    except Exception as e:
        app.logger.exception("Failed to send event to Kafka. " + str(e))
    shortcircuit_send_event(event)

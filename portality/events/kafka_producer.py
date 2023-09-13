import json
from kafka import KafkaProducer
from portality.core import app
from portality import app_email
from portality.events.shortcircuit import send_event as shortcircuit_send_event
from portality.events.system_status_check import KafkaStatusCheck

from portality.core import app as doajapp
bootstrap_server = doajapp.config.get("KAFKA_BOOTSTRAP_SERVER")

def handle_exception(error_msg, exception):
    app.logger.exception(error_msg + str(exception))
    app_email.send_mail(
        to=[app.config.get('ADMIN_EMAIL', 'sysadmin@cottagelabs.com')],
        fro=app.config.get('SYSTEM_EMAIL_FROM', 'helpdesk@doaj.org'),
        subject='Alert: DOAJ Kafka send event error',
        msg_body=error_msg + ": \n" + str(exception)
    )

producer = None

def kafka_producer():
    global producer
    try:
        if producer is None:
            producer = KafkaProducer(bootstrap_servers=bootstrap_server, value_serializer=lambda v: json.dumps(v).encode('utf-8'))
    except Exception as exp:
        producer = None
        handle_exception("Error in setting up kafka connection", exp)
    return producer

try:
    kafka_status = KafkaStatusCheck()
except Exception as exp:
    kafka_status = None
    handle_exception("Error in setting up Redis for kafka events", exp)


def send_event(event):
    try:
        if kafka_status and kafka_status.is_active() and kafka_producer():
            future = producer.send('events', value=event.serialise())
            future.get(timeout=60)
        else:
            shortcircuit_send_event(event)
    except Exception as e:
        try:
            kafka_status.set_kafka_inactive_redis()
        except Exception as exp:
            handle_exception("Failed to set kafka inactive status in Redis", exp)
        shortcircuit_send_event(event)
        handle_exception("Failed to send event to Kafka.", e)

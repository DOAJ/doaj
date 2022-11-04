import json
from kafka import KafkaProducer

from portality.core import app as doajapp
bootstrap_server = doajapp.config.get("KAFKA_BOOTSTRAP_SERVER")

producer = KafkaProducer(bootstrap_servers=bootstrap_server, value_serializer=lambda v: json.dumps(v).encode('utf-8'))


def send_event(event):
    future = producer.send('events', value=event.serialise())
    future.get(timeout=60)
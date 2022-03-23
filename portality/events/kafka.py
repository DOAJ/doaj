import faust
import json
from kafka import KafkaProducer

from portality.core import app as doajapp
from portality.bll import DOAJ
from portality.models import Event

broker = doajapp.config.get("KAFKA_BROKER")
topic_name = doajapp.config.get("KAFKA_EVENTS_TOPIC")
bootstrap_server = doajapp.config.get("KAFKA_BOOTSTRAP_SERVER")

app = faust.App('events', broker=broker, value_serializer='json')
topic = app.topic(topic_name)

producer = KafkaProducer(bootstrap_servers=bootstrap_server, value_serializer=lambda v: json.dumps(v).encode('utf-8'))


def send_event(event):
    future = producer.send('events', value=event.serialise())
    future.get(timeout=60)


@app.agent(topic)
async def handle_event(stream):
    svc = DOAJ.eventsService()
    async for event in stream:
        await svc.consume(Event(raw=json.loads(event)))


if __name__ == '__main__':
    app.main()
import faust
import json

from portality.app import app as doajapp
from portality.bll import DOAJ
from portality.models import Event

broker = doajapp.config.get("KAFKA_BROKER")
topic_name = doajapp.config.get("KAFKA_EVENTS_TOPIC")

app = faust.App('events', broker=broker, value_serializer='json')
topic = app.topic(topic_name)

event_counter = 0


@app.agent(topic)
async def handle_event(stream):
    global event_counter
    with doajapp.test_request_context("/"):
        svc = DOAJ.eventsService()
        async for event in stream:
            event_counter += 1
            doajapp.logger.info(f"Kafka event count {event_counter}")
            # TODO uncomment the following line once the Event model is fixed to Kafka
            # svc.consume(Event(raw=json.loads(event)))


if __name__ == '__main__':
    app.main()

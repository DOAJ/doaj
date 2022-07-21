import faust
import json

from portality.app import app as doajapp
from portality.bll import DOAJ
from portality.models import Event

broker = doajapp.config.get("KAFKA_BROKER")
topic_name = doajapp.config.get("KAFKA_EVENTS_TOPIC")

app = faust.App('events', broker=broker, value_serializer='json')
topic = app.topic(topic_name)


@app.agent(topic)
async def handle_event(stream):
    with doajapp.test_request_context("/"):
        svc = DOAJ.eventsService()
        async for event in stream:
            svc.consume(Event(raw=json.loads(event)))


if __name__ == '__main__':
    app.main()

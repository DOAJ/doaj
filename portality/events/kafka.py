import faust
import asyncio

from portality.core import app as doajapp
from portality.bll import DOAJ

broker = doajapp.config.get("KAFKA_BROKER")
topic_name = doajapp.config.get("KAFKA_EVENTS_TOPIC")

app = faust.App('events', broker=broker, value_serializer='json')
topic = app.topic(topic_name)


def send_event(event):
    loop = asyncio.get_event_loop()
    t = loop.create_task(topic.send(value=event.serialise()))
    r = loop.run_until_complete(t)


@app.agent(topic)
async def handle_event(stream):
    svc = DOAJ.eventsService()
    async for event in stream:
        await svc.consume(event)


if __name__ == '__main__':
    app.main()
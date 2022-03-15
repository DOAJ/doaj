import faust
import asyncio

from portality.core import app
from portality.bll import DOAJ

broker = app.config.get("KAFKA_BROKER")
topic_name = app.config.get("KAFKA_EVENTS_TOPIC")

handler = faust.App('events', broker=broker, value_serializer='json')
topic = handler.topic(topic_name)


def send_event(event):
    loop = asyncio.get_event_loop()
    t = loop.create_task(topic.send(value=event.serialise()))
    r = loop.run_until_complete(t)


@handler.agent(topic)
async def handle_event(stream):
    svc = DOAJ.eventsService()
    async for event in stream:
        await svc.consume(event)


if __name__ == '__main__':
    handler.main()
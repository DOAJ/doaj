from portality.events.consumer import EventConsumer


class MockConsumer(EventConsumer):
    ID = "mock:consumer"

    CONSUME_RESULT = True
    CONSUME_ERROR = ""

    CONSUMES = []
    CONSUMED = []

    @classmethod
    def consumes(cls, event):
        cls.CONSUMES.append(event)
        return cls.CONSUME_RESULT

    @classmethod
    def consume(cls, event):
        cls.CONSUMED.append(event)
        if cls.CONSUME_ERROR:
            raise Exception(cls.CONSUME_ERROR)

    @classmethod
    def reset(cls):
        cls.CONSUMES.clear()
        cls.CONSUMED.clear()
        cls.CONSUME_RESULT = True
        cls.CONSUME_ERROR = ""

class EventConsumer(object):
    # subclass must provide an ID
    ID = None

    @classmethod
    def consumes(cls, event):
        raise NotImplementedError()

    @classmethod
    def consume(cls, event):
        raise NotImplementedError()
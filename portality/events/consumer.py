class EventConsumer(object):
    @classmethod
    def consumes(cls, event):
        raise NotImplementedError()

    @classmethod
    def consume(cls, event):
        raise NotImplementedError()
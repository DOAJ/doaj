class EventConsumer(object):
    def consumes(self, event):
        raise NotImplementedError()

    def consume(self, event):
        raise NotImplementedError()
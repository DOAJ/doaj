class EventConsumer(object):
    # subclass must provide an ID
    ID = None

    @classmethod
    def consumes(cls, event) -> bool:
        """
        Determine whether this consumer should consume the given event
        """
        raise NotImplementedError()

    @classmethod
    def consume(cls, event) -> None:
        """
        run operation to consume and handle the event
        """
        raise NotImplementedError()
from portality.tasks.helpers import background_helper


def add_queue_info(record):
    """ Lookup the queue type for a background job and add it to an existing record """
    record.queue_type = background_helper.lookup_queue_for_action(record.action)
    return record

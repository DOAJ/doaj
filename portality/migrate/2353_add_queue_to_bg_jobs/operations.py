from portality.tasks.helpers import background_helper


def add_queue_info(record):
    """ Lookup the queue ID for a background job and add it to an existing record """
    record.queue_id = background_helper.lookup_queue_for_action(record.action)
    return record

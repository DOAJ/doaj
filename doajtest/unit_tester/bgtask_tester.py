from typing import Type

from portality import constants
from portality.background import BackgroundTask


def test_queue_id_assigned(bgtask_class: Type[BackgroundTask]):
    job = bgtask_class.prepare('just a username')
    assert job.queue_id in {constants.BGJOB_QUEUE_ID_EVENTS,
                              constants.BGJOB_QUEUE_ID_SCHEDULED_LONG,
                                constants.BGJOB_QUEUE_ID_SCHEDULED_SHORT}

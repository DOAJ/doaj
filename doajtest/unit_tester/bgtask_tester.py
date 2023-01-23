from typing import Type

from portality import constants
from portality.background import BackgroundTask


def test_queue_id_assigned(bgtask_class: Type[BackgroundTask]):
    job = bgtask_class.prepare('just a username')
    assert job.queue_id in {constants.BGJOB_QUEUE_ID_MAIN,
                              constants.BGJOB_QUEUE_ID_LONG}

from unittest import TestCase

from huey.exceptions import TaskException

from portality.lib import dates
from portality.tasks.redis_huey import TimestampedRedisHuey


class TestTimestampedRedisHuey(TestCase):
    def test_01_failed_task_error_has_timestamp(self):
        # immediate mode runs tasks in-process against memory storage, through the same error path as the consumer
        huey = TimestampedRedisHuey("test_timestamped_errors", immediate=True)

        @huey.task()
        def failing_task():
            raise ValueError("index is down")

        before = dates.now_str_with_microseconds()
        with self.assertRaises(TaskException) as cm:
            failing_task().get()
        after = dates.now_str_with_microseconds()

        error = cm.exception.metadata
        assert "index is down" in error["error"]
        assert before <= error["timestamp"] <= after

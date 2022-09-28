from unittest import TestCase

import huey.api

from doajtest import helpers
from portality import constants
from portality.core import app
from portality.tasks.helpers import background_helper
from portality.tasks.helpers.background_helper import RedisHueyTaskHelper
from portality.tasks.redis_huey import long_running, main_queue


class TestBackgroundHelper(TestCase):

    def test_get_queue_type_by_task_queue(self):
        cases = [
            (long_running, constants.BGJOB_QUEUE_TYPE_LONG),
            (main_queue, constants.BGJOB_QUEUE_TYPE_MAIN),
            (None, constants.BGJOB_QUEUE_TYPE_UNKNOWN),
            ('', constants.BGJOB_QUEUE_TYPE_UNKNOWN),
        ]

        for case in cases:
            with self.subTest(case=case):
                task_queue, excepted = case
                result = background_helper.get_queue_type_by_task_queue(task_queue)
                assert excepted == result


class TestRedisHueyTaskHelper(TestCase):
    task_name_a = '__new_schedule_a'
    task_name_b = '__new_schedule_b'
    task_name_schedule_not_exist = '___schedule_that_not_existssssss'
    expected_retries = 9292

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.org_config = helpers.patch_config(app, {
            'HUEY_SCHEDULE': {
                cls.task_name_a: {"month": "2", "day": "31", "day_of_week": "*", "hour": "*", "minute": "*"}
            }
        })

        cls.org_config = helpers.patch_config(app, {
            'HUEY_TASKS': {
                cls.task_name_b: {'retries': cls.expected_retries}
            }
        })

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        helpers.patch_config(app, cls.org_config)

    def test_register_schedule(self):
        helper = RedisHueyTaskHelper(main_queue, self.task_name_a)

        @helper.register_schedule
        def _fn():
            print('fake fn')

        assert isinstance(_fn, huey.api.TaskWrapper)

    def test_register_schedule__schedule_not_found(self):
        helper = RedisHueyTaskHelper(main_queue, self.task_name_schedule_not_exist)
        with self.assertRaises(RuntimeError):
            @helper.register_schedule
            def _fn():
                print('fake fn')

    def test_register_execute(self):
        helper = RedisHueyTaskHelper(main_queue, self.task_name_b)

        @helper.register_execute(is_load_config=True)
        def _fn():
            print('fake fn')

        assert isinstance(_fn, huey.api.TaskWrapper)
        assert _fn.retries == self.expected_retries

    def test_register_execute__config_not_found(self):
        helper = RedisHueyTaskHelper(main_queue, self.task_name_schedule_not_exist)

        with self.assertRaises(RuntimeError):
            @helper.register_execute(is_load_config=True)
            def _fn():
                print('fake fn')

    def test_register_execute__without_load_config(self):
        helper = RedisHueyTaskHelper(main_queue, self.task_name_schedule_not_exist)

        @helper.register_execute(is_load_config=False)
        def _fn():
            print('fake fn')

        assert isinstance(_fn, huey.api.TaskWrapper)

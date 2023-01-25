from unittest import TestCase

import huey.api

from doajtest import helpers
from portality import constants
from portality.core import app
from portality.tasks.helpers import background_helper
from portality.tasks.redis_huey import long_running, main_queue


class TestBackgroundHelper(TestCase):

    def test_get_queue_id_by_task_queue(self):
        cases = [
            (long_running, constants.BGJOB_QUEUE_ID_LONG),
            (main_queue, constants.BGJOB_QUEUE_ID_MAIN),
            (None, constants.BGJOB_QUEUE_ID_UNKNOWN),
        ]

        for case in cases:
            with self.subTest(case=case):
                task_queue, excepted = case
                result = background_helper.get_queue_id_by_task_queue(task_queue)
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
                cls.task_name_a: constants.CRON_NEVER,
            },
            'HUEY_TASKS': {
                cls.task_name_b: {'retries': cls.expected_retries}
            }
        })

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        helpers.patch_config(app, cls.org_config)

    def test_register_schedule(self):
        helper = background_helper.RedisHueyTaskHelper(main_queue, self.task_name_a)

        @helper.register_schedule
        def _fn():
            print('fake fn')

        assert isinstance(_fn, huey.api.TaskWrapper)

    def test_register_schedule__schedule_not_found(self):
        helper = background_helper.RedisHueyTaskHelper(main_queue, self.task_name_schedule_not_exist)
        with self.assertRaises(RuntimeError):
            @helper.register_schedule
            def _fn():
                print('fake fn')

    def test_register_execute(self):
        helper = background_helper.RedisHueyTaskHelper(main_queue, self.task_name_b)

        @helper.register_execute(is_load_config=True)
        def _fn():
            print('fake fn')

        assert isinstance(_fn, huey.api.TaskWrapper)
        assert _fn.retries == self.expected_retries

    def test_register_execute__config_not_found(self):
        helper = background_helper.RedisHueyTaskHelper(main_queue, self.task_name_schedule_not_exist)

        with self.assertRaises(RuntimeError):
            @helper.register_execute(is_load_config=True)
            def _fn():
                print('fake fn')

    def test_register_execute__without_load_config(self):
        helper = background_helper.RedisHueyTaskHelper(main_queue, self.task_name_schedule_not_exist)

        @helper.register_execute(is_load_config=False)
        def _fn():
            print('fake fn')

        assert isinstance(_fn, huey.api.TaskWrapper)


class BackgroundHelperTest(TestCase):
    DEFAULT_VALUE = 'default_value'

    def setUp(self) -> None:
        self.obj_a = dict(key_a=11223, key_none=None, key_empty='')

    def test_get_value_safe__get_value(self):
        v = background_helper.get_value_safe('key_a', self.DEFAULT_VALUE, self.obj_a)
        assert v == 11223

    def test_get_value_safe__none(self):
        v = background_helper.get_value_safe('key_none', self.DEFAULT_VALUE, self.obj_a)
        assert v == self.DEFAULT_VALUE

    def test_get_value_safe__empty(self):
        v = background_helper.get_value_safe('key_empty', self.DEFAULT_VALUE, self.obj_a)
        assert v != self.DEFAULT_VALUE

    def test_get_value_safe__default_cond_fn(self):
        v = background_helper.get_value_safe('key_empty', self.DEFAULT_VALUE, self.obj_a,
                                             default_cond_fn=lambda v: v == '')
        assert v == self.DEFAULT_VALUE

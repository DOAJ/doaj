from unittest import TestCase

from portality.tasks.helpers import background_helper


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
